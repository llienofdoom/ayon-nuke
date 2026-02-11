import nuke

from ayon_core.pipeline import load
from ayon_nuke.api import (
    containerise,
    update_container,
    viewer_update_and_undo_stop,
)


class LoadAudio(load.LoaderPlugin):
    """Load audio file into Nuke"""

    product_types = {"audio"}
    representations = {"*"}
    extensions = {"wav", "mp3", "aiff", "aif", "flac", "ogg", "m4a"}

    label = "Load Audio"
    order = -9
    icon = "volume-up"
    color = "white"

    node_name_template = "{class_name}_{ext}"

    def load(self, context, name, namespace, options):
        repre_entity = context["representation"]
        version_entity = context["version"]

        version_attributes = version_entity["attrib"]
        repre_id = repre_entity["id"]

        self.log.debug(
            "Representation id `{}` ".format(repre_id))

        # Fallback to folder name when namespace is None
        if namespace is None:
            namespace = context["folder"]["name"]

        filepath = self.filepath_from_context(context)

        if not filepath:
            self.log.warning(
                "Representation id `{}` is failing to load".format(repre_id))
            return

        filepath = filepath.replace("\\", "/")

        audio_name = self._get_node_name(context)

        # Create the AudioRead node with the filename path set
        with viewer_update_and_undo_stop():
            audio_node = nuke.createNode(
                "AudioRead", "name {}".format(audio_name), inpanel=False
            )

            audio_node["file"].setValue(filepath)
            audio_node["tile_color"].setValue(int("0x4169e1ff", 16))

            # add attributes from the version to imprint metadata knob
            data_imprint = {
                "version": version_entity["version"]
            }
            for k in ["source", "fps"]:
                data_imprint[k] = version_attributes.get(k, str(None))

            return containerise(
                audio_node,
                name=name,
                namespace=namespace,
                context=context,
                loader=self.__class__.__name__,
                data=data_imprint,
            )

    def switch(self, container, context):
        self.update(container, context)

    def update(self, container, context):
        """Update the Audio loader's path"""
        audio_node = container["node"]

        assert audio_node.Class() == "AudioRead", "Must be AudioRead"

        version_entity = context["version"]
        repre_entity = context["representation"]

        filepath = self.filepath_from_context(context)

        if not filepath:
            repre_id = repre_entity["id"]
            self.log.warning(
                "Representation id `{}` is failing to load".format(repre_id))
            return

        filepath = filepath.replace("\\", "/")

        # Set the audio file path
        audio_node["file"].setValue(filepath)

        version_attributes = version_entity["attrib"]
        updated_dict = {
            "representation": repre_entity["id"],
            "version": str(version_entity["version"]),
            "source": version_attributes.get("source"),
            "fps": str(version_attributes.get("fps")),
        }

        # Update the imprinted representation
        update_container(audio_node, updated_dict)
        self.log.info("updated to version: {}".format(
            version_entity["version"]
        ))

    def remove(self, container):
        node = container["node"]
        assert node.Class() == "AudioRead", "Must be AudioRead"

        with viewer_update_and_undo_stop():
            nuke.delete(node)

    def _get_node_name(self, context):
        folder_entity = context["folder"]
        product_name = context["product"]["name"]
        repre_entity = context["representation"]

        folder_name = folder_entity["name"]
        repre_cont = repre_entity["context"]
        name_data = {
            "folder": {
                "name": folder_name,
            },
            "product": {
                "name": product_name,
            },
            "asset": folder_name,
            "subset": product_name,
            "representation": repre_entity["name"],
            "ext": repre_cont["representation"],
            "id": repre_entity["id"],
            "class_name": self.__class__.__name__
        }

        return self.node_name_template.format(**name_data)
