"""DEM-relative camera contracts. Pure Python, no Unreal import or launch.
shots(height,bounds) -> list of dict(name,location,rotation,fov,aim).
Units cm; rotation is (pitch,yaw,roll) explicitly, NOT positional UE Rotator.
Bounds order is xmin,ymin,xmax,ymax. Parent applies named Rotator arguments.
"""
import math
def shots(height,bounds):
    xmin,ymin,xmax,ymax=map(float,bounds)
    assert xmin<xmax and ymin<ymax and callable(height)
    def ground(x,y):
        assert xmin<=x<=xmax and ymin<=y<=ymax,(x,y)
        z=float(height(x,y));assert math.isfinite(z)
        return z
    def position(x,y,above):
        x=max(xmin+500,min(xmax-500,x));y=max(ymin+500,min(ymax-500,y))
        return (x,y,ground(x,y)+above)
    def shot(name,camera,aim,fov):
        dx,dy,dz=[b-a for a,b in zip(camera,aim)]
        return dict(name=name,location=camera,rotation=(math.degrees(math.atan2(dz,math.hypot(dx,dy))),math.degrees(math.atan2(dy,dx)),0),fov=fov,aim=aim)
    # Look diagonally down the central run across trail-side mature groves.
    # Keep actual remote DEM peaks in the upper frame instead of top-down dunes.
    aim=position(30000,7000,2500)
    overview=position(-42000,-41000,24500)
    # Clearance proof along view segment. Raise camera if a DEM ridge occludes it.
    required=overview[2]
    for i in range(1,18):
        t=i/20
        x=overview[0]+(aim[0]-overview[0])*t
        y=overview[1]+(aim[1]-overview[1])*t
        required=max(required,(ground(x,y)+1800-t*aim[2])/(1-t))
    overview=(overview[0],overview[1],required)
    # Actual spawned skier at reset, small offset camera reveals skis and scenery.
    skier=position(-8500,0,170)
    camera=position(-10500,-1150,800)
    return [shot("overview",overview,aim,69),
            shot("player-level",camera,skier,62)]
