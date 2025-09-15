from flask import Blueprint, render_template
from ..models.user import User
from ..config import Config

bp = Blueprint("portal", __name__)

@bp.get("/")
def index():
    return render_template("index.html", church_lat=Config.CHURCH_LAT, church_lon=Config.CHURCH_LON)

@bp.get("/portal/<int:user_id>")
def portal(user_id: int):
    u = User.query.get_or_404(user_id)
    if u.role == "driver":
        return render_template("portal_driver.html", u=u, church_lat=Config.CHURCH_LAT, church_lon=Config.CHURCH_LON)
    elif u.role == "passenger":
        return render_template("portal_passenger.html", u=u, church_lat=Config.CHURCH_LAT, church_lon=Config.CHURCH_LON)
    else:
        # admin pourrait aussi avoir son propre portail, mais on garde le dashboard dédié
        return render_template("index.html", church_lat=Config.CHURCH_LAT, church_lon=Config.CHURCH_LON)
