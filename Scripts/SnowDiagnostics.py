"""Owner-only unsaved diagnostic selector. Import performs no UE work.
Owner runs camera AB first, begin, select/capture pairs, restore in finally.
Never save material/map. All compile/fallback gates remain owner's obligation.
"""
import unreal as u
import json,hashlib
from pathlib import Path
D=Path("D:/FallLine/Saved/Logs/SnowDiagnostics-155f6631")
L=u.MaterialEditingLibrary
S=None
def disk():
 for name,row in json.loads((D/"backups.json").read_text()).items():
  for p in [name,row["backup"]]:
   assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==row["sha256"],p
def props():
 P=u.MaterialProperty
 return [P.MP_BASE_COLOR,P.MP_ROUGHNESS,P.MP_NORMAL,P.MP_SPECULAR,P.MP_EMISSIVE_COLOR]
def graph(m):
 return {"nodes":{n.get_name():[x.get_name() if x else None for x in L.get_inputs_for_material_expression(m,n)] for n in L.get_material_expressions(m)},
 "outputs":{str(p):(L.get_material_property_input_node(m,p).get_name() if L.get_material_property_input_node(m,p) else None) for p in props()},
 "masks":{n.get_name():{k:bool(n.get_editor_property(k)) for k in ("r","g","b","a")}
 for n in L.get_material_expressions(m) if isinstance(n,u.MaterialExpressionComponentMask)},
 "output_pins":{str(p):L.get_material_property_input_node_output_name(m,p) for p in props()},
 "tangent":m.get_editor_property("tangent_space_normal")}
def variants():
 return json.loads((D/"variants.json").read_text())
def begin(metadata):
 global S
 assert S is None
 assert set(metadata)=={"player","overview"}
 for v in metadata.values():
  for k in ["camera","pose","exposure","render_size","settle_policy"]:
   assert k in v and v[k] is not None
 disk()
 m=u.load_asset("/Game/Environment/Snow/M_AlpineSnow")
 assert m and not m.get_editor_property("tangent_space_normal")
 sh=m.get_editor_property("shading_model")
 assert sh==u.MaterialShadingModel.MSM_DEFAULT_LIT
 assert L.get_material_property_input_node(m,u.MaterialProperty.MP_EMISSIVE_COLOR) is None
 nodes=list(L.get_material_expressions(m))
 # Resolve from actual material roots, never expression order or global count.
 b=variants()["baseline"]
 P=u.MaterialProperty
 rgb=L.get_material_property_input_node(m,P.MP_BASE_COLOR)
 rough=L.get_material_property_input_node(m,P.MP_ROUGHNESS)
 n=L.get_material_property_input_node(m,P.MP_NORMAL)
 assert isinstance(rgb,u.MaterialExpressionComponentMask)
 assert isinstance(rough,u.MaterialExpressionComponentMask)
 color_links=list(L.get_inputs_for_material_expression(m,rgb))
 rough_links=list(L.get_inputs_for_material_expression(m,rough))
 assert len(color_links)==1 and color_links[0]
 c=color_links[0]
 assert rough_links==[c], "Roughness must share connected baseline color"
 assert isinstance(c,u.MaterialExpressionCustom) and isinstance(n,u.MaterialExpressionCustom)
 assert c!=n and c in nodes and n in nodes
 assert c.get_editor_property("code")==b["color"]
 assert n.get_editor_property("code")==b["normal"]
 assert c.get_editor_property("output_type")==u.CustomMaterialOutputType.CMOT_FLOAT4
 assert n.get_editor_property("output_type")==u.CustomMaterialOutputType.CMOT_FLOAT3
 assert {k:bool(rgb.get_editor_property(k)) for k in ("r","g","b","a")}==dict(r=True,g=True,b=True,a=False)
 # Preserve actual G+A roughness baseline. This is NOT an A-only correction.
 assert {k:bool(rough.get_editor_property(k)) for k in ("r","g","b","a")}==dict(r=False,g=True,b=False,a=True)
 pairs=list(zip(n.get_editor_property("inputs"),L.get_inputs_for_material_expression(m,n)))
 assert any(str(i.get_editor_property("input_name"))=="G" and isinstance(x,u.MaterialExpressionVertexNormalWS) for i,x in pairs)
 for x in (c,n):
  a=list(L.get_inputs_for_material_expression(m,x))
  assert len(a)==len(x.get_editor_property("inputs")) and all(a)
 orphan_codes={x.get_name():x.get_editor_property("code") for x in nodes
  if isinstance(x,u.MaterialExpressionCustom) and x not in (c,n)}
 S=dict(m=m,c=c,n=n,sh=sh,g=graph(m),orphan_codes=orphan_codes,metadata=json.loads(json.dumps(metadata)))
 (D/"runtime-baseline.json").write_text(json.dumps(dict(graph=S["g"],metadata=metadata,accepted=False,connected_color=c.get_name(),connected_normal=n.get_name(),orphan_codes=orphan_codes,roughness_note="Actual G+A mask preserved throughout; separate roughness diagnosis possible, no correction in this test"),indent=2))
def assert_orphans():
 actual={x.get_name():x.get_editor_property("code") for x in L.get_material_expressions(S["m"])
  if isinstance(x,u.MaterialExpressionCustom) and x not in (S["c"],S["n"])}
 assert actual==S["orphan_codes"],"Disconnected Custom nodes changed"
def reset():
 assert S
 b=variants()["baseline"]
 S["c"].set_editor_property("code",b["color"])
 S["n"].set_editor_property("code",b["normal"])
 S["m"].set_editor_property("shading_model",S["sh"])
 p=u.MaterialProperty.MP_EMISSIVE_COLOR
 if L.get_material_property_input_node(S["m"],p):
  assert L.disconnect_material_property(S["m"],p)
 assert_orphans()
 assert graph(S["m"])==S["g"]
 assert S["m"].get_editor_property("shading_model")==S["sh"]
 for k,x in [("color","c"),("normal","n")]:
  assert S[x].get_editor_property("code")==b[k]
def select(mode,metadata):
 assert S and metadata==S["metadata"],"Matched camera/pose/exposure drift"
 v=variants()[mode]
 disk()
 try:
  reset()
  S["c"].set_editor_property("code",v["color"])
  S["n"].set_editor_property("code",v["normal"])
  expected=json.loads(json.dumps(S["g"]))
  sh=S["sh"]
  if v["unlit"]:
   sh=u.MaterialShadingModel.MSM_UNLIT
   S["m"].set_editor_property("shading_model",sh)
   rgb=L.get_material_property_input_node(S["m"],u.MaterialProperty.MP_BASE_COLOR)
   assert rgb and L.connect_material_property(rgb,"",u.MaterialProperty.MP_EMISSIVE_COLOR)
   expected["outputs"][str(u.MaterialProperty.MP_EMISSIVE_COLOR)]=rgb.get_name()
  assert_orphans()
  assert graph(S["m"])==expected
  assert S["m"].get_editor_property("shading_model")==sh
  for k,x in [("color","c"),("normal","n")]:
   assert S[x].get_editor_property("code")==v[k]
  L.recompile_material(S["m"])
  (D/("runtime-"+mode+".json")).write_text(json.dumps(dict(variant=mode,
   variant_sha256=hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
   graph="PASS",shader_compile="UNVERIFIED",accepted=False,metadata=metadata,
   G="VertexNormalWS; NOT guaranteed smooth geometry",saved=False),indent=2))
 except Exception:
  reset()
  L.recompile_material(S["m"])
  raise
def restore():
 global S
 assert S
 reset()
 L.recompile_material(S["m"])
 disk()
 (D/"runtime-restored.json").write_text(json.dumps(dict(graph="RESTORED_PASS",
  disk="UNCHANGED_PASS",shader_compile="UNVERIFIED",accepted=False,saved=False)))
 S=None


def inventory_readonly():
 """Explicit owner entry. Does NOT call begin/select/reset or mutate UE objects."""
 assert S is None, "Inventory prohibited during active diagnostic session"
 disk()
 m=u.load_asset("/Game/Environment/Snow/M_AlpineSnow")
 assert m
 before=graph(m)
 b=variants()["baseline"]
 def semantic(code):
  # Whitespace-only normalization is diagnostic, never authorization to rebase.
  return hashlib.sha256(" ".join(code.split()).encode()).hexdigest()
 nodes=list(L.get_material_expressions(m))
 rows=[]
 for n in nodes:
  inputs=list(L.get_inputs_for_material_expression(m,n))
  row=dict(path=n.get_path_name(),name=n.get_name(),
   type=n.get_class().get_name(),
   input_names=list(L.get_material_expression_input_names(n)),
   input_nodes=[x.get_path_name() if x else None for x in inputs],
   output_names=list(L.get_material_expression_output_names(n)))
  if isinstance(n,u.MaterialExpressionCustom):
   code=n.get_editor_property("code")
   row.update(code=code,code_sha256=hashlib.sha256(code.encode()).hexdigest(),
    semantic_sha256=semantic(code),
    exact_baseline_matches=[k for k in ("color","normal") if code==b[k]],
    semantic_baseline_matches=[k for k in ("color","normal") if semantic(code)==semantic(b[k])],
    declared_inputs=[str(x.get_editor_property("input_name")) for x in n.get_editor_property("inputs")],
    output_type=str(n.get_editor_property("output_type")))
  if isinstance(n,u.MaterialExpressionComponentMask):
   row["mask"]={k:bool(n.get_editor_property(k)) for k in ("r","g","b","a")}
  rows.append(row)
 outputs={}
 for prop in props():
  n=L.get_material_property_input_node(m,prop)
  outputs[str(prop)]=dict(node=n.get_path_name() if n else None,
   output_name=L.get_material_property_input_node_output_name(m,prop))
 assert graph(m)==before, "Read-only inventory graph drift"
 disk()
 result=dict(readonly=True,accepted=False,shader_compile="NOT_TESTED",
  baseline_disk_and_backups="MATCH",shading_model=str(m.get_editor_property("shading_model")),
  tangent_space_normal=m.get_editor_property("tangent_space_normal"),
  expressions=rows,material_outputs=outputs,
  note="All expressions included. No count relaxation, selection, rebase, compile or asset save.")
 (D/"runtime-inventory-readonly.json").write_text(json.dumps(result,indent=2))
 return result
