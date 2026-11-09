"""Exportadores de Modelos ArchiMate (Etapa 7).

Disponibiliza exportação estruturada em:
1. Formato padrão JSON do ArchiMate 3.2.
2. Formato oficial The Open Group ArchiMate Model Exchange File Format (.xml).
3. Formato nativo da ferramenta Archi (.archimate).
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from app.models.archimate import ArchiMateModel, ArchiMateLayer


class ArchiMateExporter:
    """Exporta modelos ArchiMate em JSON estruturado, Open Group XML (.xml) e Archi Nativo (.archimate)."""

    @staticmethod
    def _sanitize_xml_id(raw_id: str, prefix: str = "id") -> str:
        """Garante que o identificador seja um xs:ID / xs:NCName válido em XML (iniciando com letra/underscore)."""
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "-", (raw_id or "").strip())
        if not cleaned:
            return f"{prefix}-item"
        if not re.match(r"^[a-zA-Z_]", cleaned):
            return f"{prefix}-{cleaned}"
        return cleaned

    @classmethod
    def to_json_dict(cls, model: ArchiMateModel) -> Dict[str, Any]:
        """Converte o modelo para o formato JSON estruturado ArchiMate 3.2."""
        return {
            "$schema": "https://www.opengroup.org/archimate/3.2/model.json",
            "identifier": model.identifier,
            "name": model.name,
            "documentation": model.documentation,
            "version": model.version,
            "metadata": {
                "author": model.metadata.author,
                "createdAt": model.metadata.createdAt,
                "standard": model.metadata.standard,
                "description": model.metadata.description,
                "architecturalStyle": model.metadata.architecturalStyle,
            },
            "elements": [
                {
                    "identifier": elem.id,
                    "name": elem.name,
                    "type": elem.type.value,
                    "layer": elem.layer.value,
                    "documentation": elem.documentation,
                    "properties": elem.properties,
                }
                for elem in model.elements
            ],
            "relationships": [
                {
                    "identifier": rel.id,
                    "name": rel.name or "",
                    "type": rel.type.value,
                    "source": rel.source,
                    "target": rel.target,
                    "documentation": rel.documentation or "",
                    "properties": rel.properties,
                }
                for rel in model.relationships
            ],
            "views": [
                {
                    "identifier": view.id,
                    "name": view.name,
                    "documentation": view.documentation or "",
                    "nodes": [
                        {
                            "elementRef": n.elementId,
                            "x": n.x,
                            "y": n.y,
                            "width": n.width,
                            "height": n.height,
                        }
                        for n in view.nodes
                    ],
                    "connections": [
                        {
                            "relationshipRef": c.relationshipId,
                            "sourceRef": c.sourceId,
                            "targetRef": c.targetId,
                        }
                        for c in view.connections
                    ],
                }
                for view in model.views
            ],
        }

    @classmethod
    def to_json_string(cls, model: ArchiMateModel) -> str:
        """Serializa o modelo ArchiMate para JSON formatado."""
        data = cls.to_json_dict(model)
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def to_opengroup_xml(cls, model: ArchiMateModel) -> str:
        """Exporta o modelo para o formato Open Group ArchiMate Model Exchange (.xml 3.0/3.2).

        Segue estritamente o schema archimate3_Diagram.xsd para importação no Archi via:
        File -> Import -> Model from Open Exchange File...
        """
        ns_uri = "http://www.opengroup.org/xsd/archimate/3.0/"
        xsi_uri = "http://www.w3.org/2001/XMLSchema-instance"

        model_id = cls._sanitize_xml_id(model.identifier, "model")

        # Elemento raiz: <model>
        root = ET.Element(
            "model",
            {
                "xmlns": ns_uri,
                "xmlns:xsi": xsi_uri,
                "identifier": model_id,
                "xsi:schemaLocation": f"{ns_uri} http://www.opengroup.org/xsd/archimate/3.0/archimate3_Diagram.xsd",
            },
        )

        # 1. Nome e Documentação
        name_elem = ET.SubElement(root, "name", {"xml:lang": "pt"})
        name_elem.text = model.name

        if model.documentation:
            doc_elem = ET.SubElement(root, "documentation", {"xml:lang": "pt"})
            doc_elem.text = model.documentation

        # Rastreia definições de propriedades globais (key -> propdef_id)
        prop_defs: Dict[str, str] = {}

        def get_propdef_id(key: str) -> str:
            if key not in prop_defs:
                slug = re.sub(r"[^a-zA-Z0-9_\-]", "-", key.strip().lower()) or f"p{len(prop_defs) + 1}"
                prop_defs[key] = f"propdef-{slug}"
            return prop_defs[key]

        # 2. Contêiner de Elementos
        elements_container = ET.SubElement(root, "elements")
        elem_id_map: Dict[str, str] = {}
        for elem in model.elements:
            xml_elem_id = cls._sanitize_xml_id(elem.id, "elem")
            elem_id_map[elem.id] = xml_elem_id
            el = ET.SubElement(
                elements_container,
                "element",
                {
                    "identifier": xml_elem_id,
                    "xsi:type": elem.type.value,
                },
            )
            el_name = ET.SubElement(el, "name", {"xml:lang": "pt"})
            el_name.text = elem.name

            if elem.documentation:
                el_doc = ET.SubElement(el, "documentation", {"xml:lang": "pt"})
                el_doc.text = elem.documentation

            if elem.properties:
                props_container = ET.SubElement(el, "properties")
                for k, v in elem.properties.items():
                    if v is None or str(v).strip() == "":
                        continue
                    pdef_id = get_propdef_id(k)
                    prop = ET.SubElement(
                        props_container,
                        "property",
                        {"propertyDefinitionRef": pdef_id},
                    )
                    prop_val = ET.SubElement(prop, "value", {"xml:lang": "pt"})
                    prop_val.text = str(v)

        # 3. Contêiner de Relacionamentos
        relationships_container = ET.SubElement(root, "relationships")
        rel_id_map: Dict[str, str] = {}
        for rel in model.relationships:
            xml_rel_id = cls._sanitize_xml_id(rel.id, "rel")
            rel_id_map[rel.id] = xml_rel_id
            src_xml_id = elem_id_map.get(rel.source, cls._sanitize_xml_id(rel.source, "elem"))
            tgt_xml_id = elem_id_map.get(rel.target, cls._sanitize_xml_id(rel.target, "elem"))
            r = ET.SubElement(
                relationships_container,
                "relationship",
                {
                    "identifier": xml_rel_id,
                    "source": src_xml_id,
                    "target": tgt_xml_id,
                    "xsi:type": rel.type.value,
                },
            )
            if rel.name:
                r_name = ET.SubElement(r, "name", {"xml:lang": "pt"})
                r_name.text = rel.name
            if rel.documentation:
                r_doc = ET.SubElement(r, "documentation", {"xml:lang": "pt"})
                r_doc.text = rel.documentation
            if rel.properties:
                props_container = ET.SubElement(r, "properties")
                for k, v in rel.properties.items():
                    if v is None or str(v).strip() == "":
                        continue
                    pdef_id = get_propdef_id(k)
                    prop = ET.SubElement(
                        props_container,
                        "property",
                        {"propertyDefinitionRef": pdef_id},
                    )
                    prop_val = ET.SubElement(prop, "value", {"xml:lang": "pt"})
                    prop_val.text = str(v)

        # 4. Contêiner de PropertyDefinitions (deve preceder <views> segundo archimate3_Model.xsd)
        if prop_defs:
            prop_defs_container = ET.SubElement(root, "propertyDefinitions")
            for key_name, pdef_id in prop_defs.items():
                pdef_el = ET.SubElement(
                    prop_defs_container,
                    "propertyDefinition",
                    {
                        "identifier": pdef_id,
                        "type": "string",
                    },
                )
                pdef_name = ET.SubElement(pdef_el, "name", {"xml:lang": "pt"})
                pdef_name.text = key_name

        # 5. Contêiner de Visões e Diagramas (archimate3_Diagram.xsd)
        if model.views:
            views_container = ET.SubElement(root, "views")
            diagrams_container = ET.SubElement(views_container, "diagrams")
            for v_idx, view in enumerate(model.views, start=1):
                view_xml_id = cls._sanitize_xml_id(view.id or f"view-{v_idx}", "view")
                v = ET.SubElement(
                    diagrams_container,
                    "view",
                    {
                        "identifier": view_xml_id,
                        "xsi:type": "Diagram",
                    },
                )
                v_name = ET.SubElement(v, "name", {"xml:lang": "pt"})
                v_name.text = view.name

                if view.documentation:
                    v_doc = ET.SubElement(v, "documentation", {"xml:lang": "pt"})
                    v_doc.text = view.documentation

                # Mapeia elementId -> identifier do <node> visual nesta view
                elem_to_node_id: Dict[str, str] = {}
                for n_idx, node in enumerate(view.nodes, start=1):
                    el_ref = elem_id_map.get(node.elementId, cls._sanitize_xml_id(node.elementId, "elem"))
                    node_xml_id = cls._sanitize_xml_id(f"node-{view_xml_id}-{node.elementId}", f"node-{n_idx}")
                    elem_to_node_id[node.elementId] = node_xml_id
                    ET.SubElement(
                        v,
                        "node",
                        {
                            "identifier": node_xml_id,
                            "elementRef": el_ref,
                            "xsi:type": "Element",
                            "x": str(max(0, int(node.x))),
                            "y": str(max(0, int(node.y))),
                            "w": str(max(20, int(node.width))),
                            "h": str(max(20, int(node.height))),
                        },
                    )

                # Exporta as conexões visuais referenciando os identifiers dos <node>
                for c_idx, conn in enumerate(view.connections, start=1):
                    src_node_id = elem_to_node_id.get(conn.sourceId)
                    tgt_node_id = elem_to_node_id.get(conn.targetId)
                    rel_ref = rel_id_map.get(conn.relationshipId, cls._sanitize_xml_id(conn.relationshipId, "rel"))
                    if src_node_id and tgt_node_id:
                        conn_xml_id = cls._sanitize_xml_id(
                            f"conn-{view_xml_id}-{conn.relationshipId}", f"conn-{c_idx}"
                        )
                        ET.SubElement(
                            v,
                            "connection",
                            {
                                "identifier": conn_xml_id,
                                "relationshipRef": rel_ref,
                                "xsi:type": "Relationship",
                                "source": src_node_id,
                                "target": tgt_node_id,
                            },
                        )

        ET.indent(root, space="  ", level=0)
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_body = ET.tostring(root, encoding="utf-8").decode("utf-8")
        return xml_declaration + xml_body

    @classmethod
    def to_archi_native(cls, model: ArchiMateModel) -> str:
        """Exporta o modelo no formato nativo EMF do Archi (.archimate).

        Pode ser aberto diretamente no Archi via File -> Open... (ou duplo clique no arquivo .archimate).
        """
        archimate_ns = "http://www.archimatetool.com/archimate"
        xsi_uri = "http://www.w3.org/2001/XMLSchema-instance"

        model_id = cls._sanitize_xml_id(model.identifier, "model")
        root = ET.Element(
            "archimate:model",
            {
                "xmlns:xsi": xsi_uri,
                "xmlns:archimate": archimate_ns,
                "name": model.name,
                "id": model_id,
                "version": "5.0.0",
            },
        )

        # Hierarquia padrão de pastas do Archi
        folder_strategy = ET.SubElement(
            root, "folder", {"name": "Strategy", "id": "id-folder-strategy", "type": "strategy"}
        )
        folder_business = ET.SubElement(
            root, "folder", {"name": "Business", "id": "id-folder-business", "type": "business"}
        )
        folder_application = ET.SubElement(
            root, "folder", {"name": "Application", "id": "id-folder-application", "type": "application"}
        )
        folder_technology = ET.SubElement(
            root, "folder", {"name": "Technology & Physical", "id": "id-folder-technology", "type": "technology"}
        )
        ET.SubElement(
            root, "folder", {"name": "Motivation", "id": "id-folder-motivation", "type": "motivation"}
        )
        folder_impl = ET.SubElement(
            root,
            "folder",
            {"name": "Implementation & Migration", "id": "id-folder-impl", "type": "implementation_migration"},
        )
        folder_other = ET.SubElement(
            root, "folder", {"name": "Other", "id": "id-folder-other", "type": "other"}
        )
        folder_relations = ET.SubElement(
            root, "folder", {"name": "Relations", "id": "id-folder-relations", "type": "relations"}
        )
        folder_views = ET.SubElement(
            root, "folder", {"name": "Views", "id": "id-folder-views", "type": "diagrams"}
        )

        elem_id_map: Dict[str, str] = {}
        for elem in model.elements:
            e_id = cls._sanitize_xml_id(elem.id, "id-elem")
            elem_id_map[elem.id] = e_id

            if elem.layer == ArchiMateLayer.BUSINESS:
                target_folder = folder_business
            elif elem.layer in (ArchiMateLayer.APPLICATION, ArchiMateLayer.CHANNEL):
                target_folder = folder_application
            elif elem.layer in (ArchiMateLayer.TECHNOLOGY, ArchiMateLayer.PHYSICAL):
                target_folder = folder_technology
            elif elem.layer == ArchiMateLayer.STRATEGY:
                target_folder = folder_strategy
            elif elem.layer == ArchiMateLayer.IMPLEMENTATION_MIGRATION:
                target_folder = folder_impl
            else:
                target_folder = folder_other

            el_node = ET.SubElement(
                target_folder,
                "element",
                {
                    "xsi:type": f"archimate:{elem.type.value}",
                    "name": elem.name,
                    "id": e_id,
                },
            )
            if elem.documentation:
                doc_node = ET.SubElement(el_node, "documentation")
                doc_node.text = elem.documentation
            if elem.properties:
                for k, v in elem.properties.items():
                    if v is None or str(v).strip() == "":
                        continue
                    ET.SubElement(el_node, "property", {"key": str(k), "value": str(v)})

        rel_id_map: Dict[str, str] = {}
        for rel in model.relationships:
            r_id = cls._sanitize_xml_id(rel.id, "id-rel")
            rel_id_map[rel.id] = r_id
            src_id = elem_id_map.get(rel.source, cls._sanitize_xml_id(rel.source, "id-elem"))
            tgt_id = elem_id_map.get(rel.target, cls._sanitize_xml_id(rel.target, "id-elem"))

            rel_type_name = rel.type.value
            if not rel_type_name.endswith("Relationship"):
                rel_type_name = f"{rel_type_name}Relationship"

            rel_attrs = {
                "xsi:type": f"archimate:{rel_type_name}",
                "id": r_id,
                "source": src_id,
                "target": tgt_id,
            }
            if rel.name:
                rel_attrs["name"] = rel.name

            rel_node = ET.SubElement(folder_relations, "element", rel_attrs)
            if rel.documentation:
                doc_node = ET.SubElement(rel_node, "documentation")
                doc_node.text = rel.documentation
            if rel.properties:
                for k, v in rel.properties.items():
                    if v is None or str(v).strip() == "":
                        continue
                    ET.SubElement(rel_node, "property", {"key": str(k), "value": str(v)})

        # Diagramas / Views
        for v_idx, view in enumerate(model.views, start=1):
            v_id = cls._sanitize_xml_id(view.id or f"view-{v_idx}", "id-view")
            diag_el = ET.SubElement(
                folder_views,
                "element",
                {
                    "xsi:type": "archimate:ArchimateDiagramModel",
                    "name": view.name,
                    "id": v_id,
                },
            )

            elem_to_diag_obj_id: Dict[str, str] = {}
            for node in view.nodes:
                elem_to_diag_obj_id[node.elementId] = cls._sanitize_xml_id(
                    f"diag-obj-{v_id}-{node.elementId}", "id-dobj"
                )

            incoming_conn_ids: Dict[str, List[str]] = {node.elementId: [] for node in view.nodes}
            outgoing_conns: Dict[str, List[Dict[str, str]]] = {node.elementId: [] for node in view.nodes}

            for c_idx, conn in enumerate(view.connections, start=1):
                if conn.sourceId in elem_to_diag_obj_id and conn.targetId in elem_to_diag_obj_id:
                    c_id = cls._sanitize_xml_id(
                        f"diag-conn-{v_id}-{conn.relationshipId}", f"id-dconn-{c_idx}"
                    )
                    incoming_conn_ids[conn.targetId].append(c_id)
                    outgoing_conns[conn.sourceId].append(
                        {
                            "id": c_id,
                            "source": elem_to_diag_obj_id[conn.sourceId],
                            "target": elem_to_diag_obj_id[conn.targetId],
                            "archimateRelationship": rel_id_map.get(
                                conn.relationshipId, cls._sanitize_xml_id(conn.relationshipId, "id-rel")
                            ),
                        }
                    )

            for node in view.nodes:
                dobj_id = elem_to_diag_obj_id[node.elementId]
                arch_elem_id = elem_id_map.get(
                    node.elementId, cls._sanitize_xml_id(node.elementId, "id-elem")
                )
                child_attrs = {
                    "xsi:type": "archimate:DiagramObject",
                    "id": dobj_id,
                    "archimateElement": arch_elem_id,
                }
                if incoming_conn_ids.get(node.elementId):
                    child_attrs["targetConnections"] = " ".join(incoming_conn_ids[node.elementId])

                child_el = ET.SubElement(diag_el, "child", child_attrs)
                ET.SubElement(
                    child_el,
                    "bounds",
                    {
                        "x": str(max(0, int(node.x))),
                        "y": str(max(0, int(node.y))),
                        "width": str(max(20, int(node.width))),
                        "height": str(max(20, int(node.height))),
                    },
                )
                for out_c in outgoing_conns.get(node.elementId, []):
                    ET.SubElement(
                        child_el,
                        "sourceConnection",
                        {
                            "xsi:type": "archimate:Connection",
                            "id": out_c["id"],
                            "source": out_c["source"],
                            "target": out_c["target"],
                            "archimateRelationship": out_c["archimateRelationship"],
                        },
                    )

        if model.documentation:
            purpose_el = ET.SubElement(root, "purpose")
            purpose_el.text = model.documentation

        ET.indent(root, space="  ", level=0)
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_body = ET.tostring(root, encoding="utf-8").decode("utf-8")
        return xml_declaration + xml_body
