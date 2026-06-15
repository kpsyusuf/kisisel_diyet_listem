from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'  

@app.route("/health")
def health_check():
    return "OK", 200
 

def kalori_ihtiyaci_hesapla(kilo, boy, yas, cinsiyet, diyabet):
    try:
        kilo = float(kilo)
        boy = float(boy)
        yas = int(yas)
        diyabet = bool(int(diyabet))
    except ValueError:
        return "Hata: Geçerli bir sayı giriniz!"  

    if cinsiyet.lower() == 'erkek':
        bmr = 10 * kilo + 6.25 * boy - 5 * yas + 5
    else:
        bmr = 10 * kilo + 6.25 * boy - 5 * yas - 161

    if diyabet:
        bmr *= 0.85

    return round(bmr)

@app.route("/")
def ana_sayfa():
    if "kullanici_id" in session:
        return redirect(url_for("profil"))  # Eğer giriş yapmışsa profil sayfasına yönlendir
    return redirect(url_for("giris"))  # Eğer giriş yapmamışsa, giriş sayfasına yönlendir

@app.route("/giris", methods=["GET", "POST"])
def giris():
    if request.method == "POST":
        email = request.form["email"]
        sifre = request.form["sifre"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, SIFRE FROM KULLANICI WHERE EMAIL = ?", (email,))
        row = cursor.fetchone()
        if row and check_password_hash(row[1], sifre):
            session["kullanici_id"] = row[0]
            flash("Giriş başarılı!", "success")
            conn.close()
            return redirect(url_for("profil"))
        else:
            flash("E-posta veya şifre yanlış.", "danger")
        conn.close()
    return render_template("giris.html")

@app.route("/kayit", methods=["GET", "POST"])
def kayit():
    if request.method == "POST":
        ad = request.form["ad"]
        soyad = request.form["soyad"]
        yas = request.form["yas"]
        cinsiyet = request.form["cinsiyet"]
        boy = request.form["boy"]
        kilo = request.form["kilo"]
        diyabet = request.form["diyabet"]
        email = request.form["email"]
        sifre = generate_password_hash(request.form["sifre"])
        alerji_durumu = request.form["alerji_durumu"]

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO KULLANICI (AD, SOYAD, YAS, CINSIYET, BOY, KILO, DIYABET, EMAIL, SIFRE, ALERJI_DURUMU)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ad, soyad, yas, cinsiyet, boy, kilo, diyabet, email, sifre, alerji_durumu))
            conn.commit()

            cursor.execute("SELECT ID FROM KULLANICI WHERE EMAIL = ?", (email,))
            kullanici_id = cursor.fetchone()[0]

            if alerji_durumu == "var":
                alerji_listesi = request.form.getlist("alerjiler[]")
                for gida_id in alerji_listesi:
                    cursor.execute("INSERT INTO ALERJI (KULLANICI_ID, GIDA_ID) VALUES (?, ?)", (kullanici_id, gida_id))
                conn.commit()

            flash("Kayıt başarılı!", "success")
            return redirect(url_for("giris"))
        except Exception as e:
            conn.rollback()
            flash(f"Hata oluştu: {e}", "danger")
            return redirect(url_for("kayit"))
        finally:
            cursor.close()
            conn.close()
    return render_template("kayit.html")

@app.route("/gida-arama")
def gida_arama():
    kelime = request.args.get('kelime', '').strip()
    if not kelime or len(kelime) < 2:
        return jsonify([])
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT ID, ISIM FROM GIDA WHERE ISIM COLLATE Latin1_General_CI_AI LIKE ?"
    cursor.execute(query, (kelime + '%',))
    gidalar = [{'id': row[0], 'isim': row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(gidalar)

@app.route("/profil")
def profil():
    if "kullanici_id" not in session:
        return redirect(url_for("giris"))
    kullanici_id = session["kullanici_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT AD, SOYAD, YAS, CINSIYET, BOY, KILO, DIYABET FROM KULLANICI WHERE ID = ?", (kullanici_id,))
    row = cursor.fetchone()
    kalori_ihtiyaci = kalori_ihtiyaci_hesapla(row[5], row[4], row[2], row[3], row[6])
    kullanici_bilgileri = {
        "ad": row[0], "soyad": row[1], "yas": row[2],
        "cinsiyet": row[3], "boy": row[4], "kilo": row[5], "diyabet": row[6]
    }
    cursor.execute("""
        SELECT GIDA.ID, GIDA.ISIM
        FROM ALERJI
        JOIN GIDA ON ALERJI.GIDA_ID = GIDA.ID
        WHERE ALERJI.KULLANICI_ID = ?
    """, (kullanici_id,))
    alerjiler = [{"id": r[0], "isim": r[1]} for r in cursor.fetchall()]
    conn.close()
    return render_template("profil.html", kullanici={**kullanici_bilgileri, "alerjiler": alerjiler, "kalori_ihtiyaci": kalori_ihtiyaci})

@app.route("/profil-guncelle", methods=["POST"])
def profil_guncelle():
    if "kullanici_id" not in session:
        return redirect(url_for("giris"))
    kullanici_id = session["kullanici_id"]
    ad = request.form["ad"]
    soyad = request.form["soyad"]
    yas = request.form["yas"]
    cinsiyet = request.form["cinsiyet"]
    boy = request.form["boy"]
    kilo = request.form["kilo"]
    diyabet = int(request.form["diyabet"])
    alerji_durumu = request.form.get("alerji_durumu")
    yeni_alerjiler = request.form.getlist("alerjiler[]")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE KULLANICI SET AD = ?, SOYAD = ?, YAS = ?, CINSIYET = ?, BOY = ?, KILO = ?, DIYABET = ? WHERE ID = ?
        """, (ad, soyad, yas, cinsiyet, boy, kilo, diyabet, kullanici_id))
        
        if alerji_durumu == "var":
        
            cursor.execute("SELECT GIDA_ID FROM ALERJI WHERE KULLANICI_ID = ?", (kullanici_id,))
            mevcut = set(row[0] for row in cursor.fetchall())

            
            yeni_alerjiler = request.form.getlist("alerjiler[]")  

            for gida_id in yeni_alerjiler:
                if gida_id not in mevcut:
                    cursor.execute("INSERT INTO ALERJI (KULLANICI_ID, GIDA_ID) VALUES (?, ?)", (kullanici_id, gida_id))
        conn.commit()
        flash("Profil başarıyla güncellendi.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Hata oluştu: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("profil"))

@app.route("/alerji-sil", methods=["POST"])
def alerji_sil():
    if "kullanici_id" not in session:
        return jsonify({"success": False}), 403
    data = request.get_json()
    gida_id = data.get("gida_id")
    kullanici_id = session["kullanici_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ALERJI WHERE KULLANICI_ID = ? AND GIDA_ID = ?", (kullanici_id, gida_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/besin_sec")
def besin_sec():
    if "kullanici_id" not in session:
        return redirect(url_for("giris"))
    kullanici_id = session["kullanici_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT YAS, BOY, KILO, CINSIYET, DIYABET FROM KULLANICI WHERE ID = ?", (kullanici_id,))
    y, b, k, c, d = cursor.fetchone()
    hedef_kalori = kalori_ihtiyaci_hesapla(k, b, y, c, d)
    cursor.execute("""
        SELECT ID, ISIM, OLCUM_TURU, KALORI
        FROM GIDA
        WHERE ID NOT IN (
            SELECT GIDA_ID FROM ALERJI WHERE KULLANICI_ID = ?
        )
    """, (kullanici_id,))
    besinler = [
        {"id": row[0], "isim": row[1], "olcum_turu": row[2], "kalori": row[3]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return render_template("besin_sec.html", besinler=besinler, hedef_kalori=hedef_kalori)

@app.route("/secili_besinleri_kaydet", methods=["POST"])
def secili_besinleri_kaydet():
    if "kullanici_id" not in session:
        return redirect(url_for("giris"))
    kullanici_id = session["kullanici_id"]
    secilenler = request.form.getlist("secilen_besinler[]")
    tarih = request.form["tarih"]
    ogun_tipi = request.form["ogun_tipi"]
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for gida_id in secilenler:
            miktar_str = request.form.get(f"miktar_{gida_id}", "1")
            try:
                miktar = float(miktar_str)
            except ValueError:
                miktar = 1
            cursor.execute("""
                INSERT INTO OGUN (KULLANICI_ID, GIDA_ID, OGUN_TIPI, TARIH, MIKTAR)
                VALUES (?, ?, ?, ?, ?)
            """, (kullanici_id, gida_id, ogun_tipi, tarih, miktar))
        conn.commit()
        flash("Besinler başarıyla kaydedildi.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Hata oluştu: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("besin_sec"))

@app.route("/ogun_liste")
def ogun_liste():
    if "kullanici_id" not in session:
        return redirect(url_for("giris"))
    kullanici_id = session["kullanici_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT O.TARIH, O.OGUN_TIPI, G.ISIM, G.KALORI, G.OLCUM_TURU, O.MIKTAR
        FROM OGUN O
        JOIN GIDA G ON O.GIDA_ID = G.ID
        WHERE O.KULLANICI_ID = ?
        ORDER BY O.TARIH DESC, O.OGUN_TIPI
    """, (kullanici_id,))
    rows = cursor.fetchall()
    liste = {}
    tarih_toplamlari = {}
    for row in rows:
        tarih = row[0]
        ogun_tipi = row[1]
        isim = row[2]
        kalori = row[3]
        olcum_turu = row[4]
        miktar = row[5]
        toplam_kalori = kalori * miktar
        if tarih not in liste:
            liste[tarih] = {}
        if ogun_tipi not in liste[tarih]:
            liste[tarih][ogun_tipi] = {"besinler": [], "toplam_kalori": 0}
        liste[tarih][ogun_tipi]["besinler"].append({
            "isim": isim,
            "kalori": toplam_kalori,
            "miktar": miktar,
            "olcum_turu": olcum_turu
        })
        liste[tarih][ogun_tipi]["toplam_kalori"] += toplam_kalori
        tarih_toplamlari[tarih] = tarih_toplamlari.get(tarih, 0) + toplam_kalori
    cursor.execute("SELECT YAS, BOY, KILO, CINSIYET, DIYABET FROM KULLANICI WHERE ID = ?", (kullanici_id,))
    y, b, k, c, d = cursor.fetchone()
    cal_need = kalori_ihtiyaci_hesapla(k, b, y, c, d)
    conn.close()
    return render_template("ogun_liste.html", liste=liste, tarih_toplamlari=tarih_toplamlari, cal_need=cal_need)

@app.route("/toplam_kalori")
def toplam_kalori():
    if "kullanici_id" not in session:
        return jsonify({"toplam_kalori": 0})
    kullanici_id = session["kullanici_id"]
    tarih = request.args.get("tarih")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(G.KALORI)
        FROM OGUN O
        JOIN GIDA G ON O.GIDA_ID = G.ID
        WHERE O.KULLANICI_ID = ? AND O.TARIH = ?
    """, (kullanici_id, tarih))
    toplam = cursor.fetchone()[0]
    conn.close()
    return jsonify({"toplam_kalori": toplam if toplam else 0})

@app.route("/ogun_sil", methods=["POST"])
def ogun_sil():
    if "kullanici_id" not in session:
        return jsonify(success=False), 403
    kullanici_id = session["kullanici_id"]
    data = request.get_json()
    tarih = data.get("tarih")
    ogun_tipi = data.get("ogun_tipi")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM OGUN 
        WHERE KULLANICI_ID = ? AND TARIH = ? AND OGUN_TIPI = ?
    """, (kullanici_id, tarih, ogun_tipi))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route("/gun_sil", methods=["POST"])
def gun_sil():
    if "kullanici_id" not in session:
        return jsonify(success=False), 403
    kullanici_id = session["kullanici_id"]
    data = request.get_json()
    tarih = data.get("tarih")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM OGUN 
        WHERE KULLANICI_ID = ? AND TARIH = ?
    """, (kullanici_id, tarih))
    conn.commit()
    conn.close()
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(debug=True)
