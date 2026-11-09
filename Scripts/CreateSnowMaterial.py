"""World-space snow/rock with stochastic multi-scale sampling, no WPO.
Source textures are CC0 Poly Haven; material never changes terrain collision.
Custom expressions follow Epic UE5.8 MaterialExpressionCustom API.
"""
import unreal
import re
import json
from pathlib import Path
def create_snow():
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    base="/Game/Environment/Snow"
    textures={}
    for kind in ["diff","nor_dx","rough"]:
        path=base+"/snow_02_"+kind+"_2k"
        tex=unreal.load_asset(path)
        if not tex:
            task=unreal.AssetImportTask()
            for key,val in {"filename":"D:/FallLine/SourceAssets/PolyHaven/snow_02_"+kind+"_2k.jpg","destination_path":base,"automated":True,"save":True}.items():
                task.set_editor_property(key,val)
            tools.import_asset_tasks([task])
            tex=unreal.load_asset(path)
        assert tex,path
        if kind!="diff": tex.set_editor_property("srgb",False)
        if kind=="nor_dx": tex.set_editor_property("compression_settings",unreal.TextureCompressionSettings.TC_NORMALMAP)
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        textures[kind]=tex
    from ImportAlpineAssets import _texture
    rock={k:_texture("boulder_01",k,normal=k=="nor_dx",linear=k=="rough") for k in textures}
    mat=unreal.load_asset(base+"/M_AlpineSnow")
    if not mat: mat=tools.create_asset("M_AlpineSnow",base,unreal.Material,unreal.MaterialFactoryNew())
    # Material.h bTangentSpaceNormal: custom normal below is world-space.
    mat.set_editor_property("tangent_space_normal",False)
    lib=unreal.MaterialEditingLibrary
    lib.delete_all_material_expressions(mat)
    def node(cls): return lib.create_material_expression(mat,cls)
    world=node(unreal.MaterialExpressionWorldPosition)
    geom=node(unreal.MaterialExpressionVertexNormalWS)
    camera=node(unreal.MaterialExpressionCameraPositionWS)
    inputs={"W":world,"G":geom,"C":camera}
    for prefix,src in [("Snow",textures),("Rock",rock)]:
        for suffix,kind in [("D","diff"),("N","nor_dx"),("R","rough")]:
            obj=node(unreal.MaterialExpressionTextureObject)
            obj.set_editor_property("texture",src[kind])
            inputs[prefix+suffix]=obj
    common=r"""
struct FAlpine {
 float noise(float2 p) {
  float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);
  float a=frac(sin(dot(i,float2(127.1,311.7)))*43758.5453);
  float b=frac(sin(dot(i+float2(1,0),float2(127.1,311.7)))*43758.5453);
  float c=frac(sin(dot(i+float2(0,1),float2(127.1,311.7)))*43758.5453);
  float d=frac(sin(dot(i+1,float2(127.1,311.7)))*43758.5453);
  return lerp(lerp(a,b,f.x),lerp(c,d,f.x),f.y);
 }
 float3 normal(float4 t) {float2 xy=t.rg*2-1;return float3(xy,sqrt(saturate(1-dot(xy,xy))));}
};
FAlpine F;
float2 uv=W.xy/240;
float2 uvB=float2(uv.x*.8-uv.y*.6,uv.x*.6+uv.y*.8)*.731+float2(13.21,7.83);
float2 uvC=float2(-uv.y,uv.x)*1.317+float2(31.6,18.2);
float w=F.noise(W.xy/3200);
float v=F.noise(W.xy/7100+17);
float macro=F.noise(W.xy/19000);
float dist=length(W-C);
float fade=smoothstep(1200,18000,dist);
// Pixel geometric slope from the rendered surface, independent of landscape
// vertex-normal interpolation. ddx/ddy are pixel-stage only (no WPO).
float3 surface=normalize(cross(ddx(W),ddy(W)));
surface*=surface.z<0?-1:1;
// World units are cm. Expose mixed bedrock at 28-48 degree slopes;
// preserve flat snow, break the boundary with 12m/80m patches.
float deposit=(F.noise(W.xy/1200)-.5)*.10+(F.noise(W.xy/8000)-.5)*.08;
float cliff=1-smoothstep(.6691,.8829,abs(surface.z)+deposit);
float3 axis=pow(abs(normalize(G)),4);axis/=max(.001,axis.x+axis.y+axis.z);
"""
    albedo=common+r"""
float3 sd0=Texture2DSample(SnowD,SnowDSampler,uv).rgb;
float3 sd1=Texture2DSample(SnowD,SnowDSampler,uvB).rgb;
float3 sd2=Texture2DSample(SnowD,SnowDSampler,uvC).rgb;
float3 snow=lerp(lerp(sd0,sd1,.28+.44*w),sd2,.18+.25*v);
// Keep source grain instead of washing 58% of it into constant blue.
snow=lerp(snow,float3(.88,.90,.92),.06);
float patch=F.noise(W.xy/2400);
float broad=F.noise(W.xy/9500+11);
snow*=lerp(float3(.69,.78,.90),float3(1.0,.99,.97),smoothstep(.18,.82,patch*.7+broad*.3));
// Visible wind-crust relief lives at 0.35m / 1.8m, not subpixel crystal scale.
float crust=F.noise(W.xy/110);
float drift=F.noise(W.yz/1700)*.5+F.noise(W.xz/2900)*.5;
snow*=.80+.13*macro+.04*drift+.03*crust;
float3 rd=Texture2DSample(RockD,RockDSampler,W.yz/360).rgb*axis.x+
Texture2DSample(RockD,RockDSampler,W.xz/360).rgb*axis.y+
Texture2DSample(RockD,RockDSampler,W.xy/360).rgb*axis.z;
// Decametre rock modulation survives overview minification; local 3.6m
// texture remains near-camera. No WPO, displacement or silhouette edits.
float rockLarge=F.noise(W.xy/2400+W.z/1700);
float strata=F.noise(W.yz/2300+F.noise(W.xz/6100)*2);
float luminance=dot(rd,float3(.2126,.7152,.0722));
rd=lerp(rd,luminance*float3(.78,.84,.92),.70);
rd*=.48+.32*rockLarge+.20*smoothstep(.2,.8,strata);
float rough=Texture2DSample(SnowR,SnowRSampler,uvB).r;
// Sparse, sub-centimetre cells fade before they can shimmer in the distance.
float grain=frac(sin(dot(floor(W.xy*1.3),float2(127.1,311.7)))*43758.5453);
float crystal=smoothstep(.965,.997,grain)*(1-smoothstep(250,2200,dist));
rough=clamp(.25+rough*.24+patch*.16-crystal*.18,.20,.78);
float rr=Texture2DSample(RockR,RockRSampler,W.yz/360).r*axis.x+
Texture2DSample(RockR,RockRSampler,W.xz/360).r*axis.y+
Texture2DSample(RockR,RockRSampler,W.xy/360).r*axis.z;
rough=lerp(rough,rr,cliff);
return float4(lerp(snow,rd*.92,cliff),rough);
"""
    normal=common+r"""
// Signed world-aligned projections, identical UV scale for snow/rock.
// Decode BC5 normals and blend detail perturbations around the existing G;
// flat normal textures preserve G exactly, without displacing the surface.
float3 g=normalize(G);
float3 sg=float3(g.x<0?-1:1,g.y<0?-1:1,g.z<0?-1:1);
float3 sx=F.normal(Texture2DSample(SnowN,SnowNSampler,W.yz/240));
float3 sy=F.normal(Texture2DSample(SnowN,SnowNSampler,W.xz/240));
float3 sz=F.normal(Texture2DSample(SnowN,SnowNSampler,W.xy/240));
float3 rx=F.normal(Texture2DSample(RockN,RockNSampler,W.yz/360));
float3 ry=F.normal(Texture2DSample(RockN,RockNSampler,W.xz/360));
float3 rz=F.normal(Texture2DSample(RockN,RockNSampler,W.xy/360));
// X projection tangent Y, bitangent signed Z; Y tangent X,
// bitangent negative signed Z; Z tangent X, bitangent signed Y.
float3 snowDetail=float3(0,sx.x,sg.x*sx.y)*axis.x+
 float3(sy.x,0,-sg.y*sy.y)*axis.y+float3(sz.x,sg.z*sz.y,0)*axis.z;
float3 rockDetail=float3(0,rx.x,sg.x*rx.y)*axis.x+
 float3(ry.x,0,-sg.y*ry.y)*axis.y+float3(rz.x,sg.z*rz.y,0)*axis.z;
snowDetail-=g*dot(g,snowDetail);
rockDetail-=g*dot(g,rockDetail);
float strength=lerp(.85,.25,fade);
float3 snowWorld=normalize(g+strength*snowDetail);
float3 rockWorld=normalize(g+.75*rockDetail);
return normalize(lerp(snowWorld,rockWorld,cliff));
"""
    # Source verified in UE5.8 MaterialEditingLibrary.cpp and MaterialExpressions.cpp.
    # Connection notifications can compile an incomplete intermediate graph. A
    # successful connect return is NOT proof of final linkage or shader success.
    receipt=Path("D:/FallLine/Saved/Logs/snow-graph-runtime.json")
    receipt.write_text(json.dumps({"graph":"PENDING","shader_compile":"UNVERIFIED",
                                  "accepted":False}))
    graphs=[]
    def require(ok,message):
        if not ok:
            receipt.write_text(json.dumps({"graph":"FAIL","shader_compile":"UNVERIFIED",
                                          "accepted":False,"error":message}))
            raise RuntimeError(message)
    def linked(obj,expected):
        actual=list(lib.get_inputs_for_material_expression(mat,obj))
        require(len(actual)==len(expected) and all(a==b for a,b in zip(actual,expected)),
                "Snow graph readback mismatch: "+obj.get_name())
    def custom(code,output):
        obj=node(unreal.MaterialExpressionCustom)
        obj.set_editor_property("code",code)
        obj.set_editor_property("output_type",output)
        custom_inputs=[]
        # Bind only referenced external identifiers; texture samplers are
        # automatically generated by UE from the corresponding texture input.
        tokens=set(re.findall(r"\b[A-Za-z_]\w*\b",code))
        used={k:v for k,v in inputs.items() if k in tokens}
        for sampler in re.findall(r"\b(\w+)Sampler\b",code):
            require(sampler in used,"Undeclared texture sampler: "+sampler)
        for k in used:
            item=unreal.CustomInput()
            item.set_editor_property("input_name",k)
            custom_inputs.append(item)
        obj.set_editor_property("inputs",custom_inputs)
        require([str(x.get_editor_property("input_name")) for x in obj.get_editor_property("inputs")]==list(used),
                "Custom input names differ from requested identifiers")
        for k,value in used.items():
            require(lib.connect_material_expressions(value,"",obj,k),"Custom input connect failed: "+k)
        linked(obj,list(used.values()))
        graphs.append((obj,list(used.values())))

        return obj
    color=custom(albedo,unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    rgb=node(unreal.MaterialExpressionComponentMask)
    for k in ["r","g","b"]:rgb.set_editor_property(k,True)
    require(lib.connect_material_expressions(color,"",rgb,""),"RGB mask connection failed")
    graphs.append((rgb,[color]))
    require(lib.connect_material_property(rgb,"",unreal.MaterialProperty.MP_BASE_COLOR),"MP_BASE_COLOR connection failed")
    rough=node(unreal.MaterialExpressionComponentMask);rough.set_editor_property("a",True)
    rough.set_editor_property("r",False)
    rough.set_editor_property("g",False)
    rough.set_editor_property("b",False)
    require(lib.connect_material_expressions(color,"",rough,""),"Roughness mask connection failed")
    graphs.append((rough,[color]))
    require(lib.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS),"MP_ROUGHNESS connection failed")
    n=custom(normal,unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    require(lib.connect_material_property(n,"",unreal.MaterialProperty.MP_NORMAL),"MP_NORMAL connection failed")
    spec=node(unreal.MaterialExpressionConstant);spec.set_editor_property("r",.34)
    require(lib.connect_material_property(spec,"",unreal.MaterialProperty.MP_SPECULAR),"MP_SPECULAR connection failed")
    for obj,expected in graphs:
        linked(obj,expected)
    for prop,expected in [(unreal.MaterialProperty.MP_BASE_COLOR,rgb),
                          (unreal.MaterialProperty.MP_ROUGHNESS,rough),
                          (unreal.MaterialProperty.MP_NORMAL,n),
                          (unreal.MaterialProperty.MP_SPECULAR,spec)]:
        require(lib.get_material_property_input_node(mat,prop)==expected,
                "Material output readback mismatch: "+str(prop))
    receipt.write_text(json.dumps({"graph":"PASS","shader_compile":"UNVERIFIED",
        "accepted":False,"nodes":[{"node":obj.get_name(),
        "inputs":[v.get_name() for v in expected]} for obj,expected in graphs]},
        indent=2))
    lib.recompile_material(mat)
    lib.layout_material_expressions(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log("FALLLINE_SNOW_STOCHASTIC patch=24m/95m detail=2.4m rock=3.6m/24m strata=nonperiodic23m slope=28-48deg interpolated_lighting_normal geometric_slope_only no_WPO")
    return mat
