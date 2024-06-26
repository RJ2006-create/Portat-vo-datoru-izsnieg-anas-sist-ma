from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///datoru_izsniegšana.db'
app.config['SECRET_KEY'] = 'jūsu_slepenais_atslēgas'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Modeļi
class Skoleni(UserMixin, db.Model):
    s_id = db.Column(db.Integer, primary_key=True)
    vards = db.Column(db.String(50), nullable=False)
    uzvards = db.Column(db.String(50), nullable=False)
    klase = db.Column(db.String(10), nullable=False)
    lietotajvards = db.Column(db.String(50), unique=True, nullable=False)
    paroles_hash = db.Column(db.String(128), nullable=False)

    def uzstadit_paroli(self, parole):
        self.paroles_hash = generate_password_hash(parole)

    def parbaudit_paroli(self, parole):
        return check_password_hash(self.paroles_hash, parole)

class Datori(db.Model):
    d_id = db.Column(db.Integer, primary_key=True)
    d_numurs = db.Column(db.String(10), nullable=False)
    inv_numurs = db.Column(db.String(20), nullable=False)
    modelis = db.Column(db.String(50), nullable=False)
    kastes_numurs = db.Column(db.String(10), nullable=False)
    vieta = db.Column(db.String(10), nullable=True)

class Izsniegumi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    s_id = db.Column(db.Integer, db.ForeignKey('skoleni.s_id'), nullable=False)
    d_id = db.Column(db.Integer, db.ForeignKey('datori.d_id'), nullable=False)
    izsn_laiks = db.Column(db.DateTime, default=datetime.utcnow)
    atg_laiks = db.Column(db.DateTime, nullable=True)

# Lietotāja ielādes funkcija Flask-Login
@login_manager.user_loader
def ieladet_lietotaju(lietotaja_id):
    return Skoleni.query.get(int(lietotaja_id))

# Ceļi
@app.route('/pievienot_lietotaju', methods=['POST'])
@login_required
def pievienot_lietotaju():
    vards = request.form.get('vards')
    uzvards = request.form.get('uzvards')
    klase = request.form.get('klase')
    lietotajvards = request.form.get('lietotajvards')
    parole = request.form.get('parole')

    jaunais_lietotajs = Skoleni(vards=vards, uzvards=uzvards, klase=klase, lietotajvards=lietotajvards)
    jaunais_lietotajs.uzstadit_paroli(parole)
    db.session.add(jaunais_lietotajs)
    db.session.commit()
    flash('Lietotājs veiksmīgi pievienots.', 'success')

    return redirect(url_for('admin_panelis'))

@app.route('/dzest_lietotaju/<lietotaja_id>')
@login_required
def dzest_lietotaju(lietotaja_id):
    lietotajs = Skoleni.query.get(lietotaja_id)

    # Dzēst lietotāju un saistītos izsniegumus
    Izsniegumi.query.filter_by(s_id=lietotaja_id).delete()
    db.session.delete(lietotajs)
    db.session.commit()
    flash('Lietotajs veiksmigi dzests.', 'success')

    return redirect(url_for('admin_panelis'))


@app.route('/izsniegt_datoru', methods=['POST'])
@login_required
def izsniegt_datoru():
    s_id = request.form.get('skolena_id')
    d_id = request.form.get('datora_id')

    # Vieta: Izstrādāt vietas izvēles loģiku, pamatojoties uz jūsu dizainu
    izveleta_vieta = request.form.get('izveleta_vieta')

    # Krāsu kods: Izstrādāt krāsu koda loģiku, pamatojoties uz jūsu dizainu
    krāsu_kods = 'zaļš'

    # Pārbaudīt, vai izvēlētais dators ir pieejams
    esoss_izsniegums = Izsniegumi.query.filter_by(d_id=d_id, atg_laiks=None).first()
    if esoss_izsniegums:
        flash('Kļūda: Izvēlētais dators jau ir izsniegts.', 'danger')
    else:
        jaunais_izsniegums = Izsniegumi(s_id=s_id, d_id=d_id)
        db.session.add(jaunais_izsniegums)
        db.session.commit()
        flash('Dators izsniegts veiksmīgi.', 'success')

    return redirect(url_for('lietotaja_panelis'))

@app.route('/atgriezt_datoru/<izsnieguma_id>', methods=['GET', 'POST'])
@login_required
def atgriezt_datoru(izsnieguma_id):
    izsniegums = Izsniegumi.query.get(izsnieguma_id)

    if request.method == 'POST':
        # Atjaunināt atgriešanas laiku un mainīt pogas krāsu uz zaļo
        izsniegums.atg_laiks = datetime.utcnow()
        db.session.commit()
        flash('Dators veiksmīgi atgriezts.', 'success')

        return redirect(url_for('lietotaja_panelis'))

    return render_template('atgriezt_datoru.html', izsniegums=izsniegums)

# Citi ceļi un funkcijas

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)