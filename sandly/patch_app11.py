import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

old_qr_logic = """        if st.button("QR-Codes generieren"):
            try:
                import qrcode
                from io import BytesIO
                
                qr_cols = st.columns(3)
                idx = 0
                for grp in groups:
                    for t_id, t_name in data["teams"][grp].items():
                        token = data["team_tokens"].get(t_id, "FEHLER")
                        url = f"{base_url}/?token={token}"
                        
                        qr = qrcode.QRCode(version=1, box_size=5, border=4)
                        qr.add_data(url)
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        
                        with qr_cols[idx % 3]:
                            st.write(f"**{t_id} ({t_name})**")
                            st.image(buf.getvalue(), width=150)
                            st.write(f"`{token}`")
                            st.markdown("---")
                        idx += 1
            except ImportError:
                st.error("Bitte installiere qrcode und Pillow (pip install qrcode Pillow)")"""

new_qr_logic = """        if st.button("QR-Codes generieren & Druckversion erstellen"):
            try:
                import qrcode
                import base64
                from io import BytesIO
                
                html_content = \"\"\"<html>
                <head>
                    <meta charset="utf-8">
                    <title>Team QR Codes</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 2cm; }
                        .card { border: 2px dashed #ccc; padding: 30px; margin-bottom: 30px; text-align: center; page-break-inside: avoid; break-inside: avoid; }
                        .team-name { font-size: 28px; font-weight: bold; margin-bottom: 10px; }
                        .instruction { font-size: 18px; color: #555; margin-bottom: 20px; }
                        img { width: 350px; height: 350px; }
                        .url-text { font-family: monospace; margin-top: 15px; font-size: 14px; color: #777; }
                        @media print {
                            .card { border: 1px solid #000; page-break-inside: avoid; break-inside: avoid; }
                        }
                    </style>
                </head>
                <body>
                    <h1 style="text-align: center;">BVC Turnier - Team Logins</h1>
                \"\"\"
                
                st.success("QR-Codes wurden erfolgreich generiert! Du kannst sie hier betrachten und als druckfertige Datei herunterladen.")
                
                qr_cols = st.columns(3)
                idx = 0
                for grp in groups:
                    for t_id, t_name in data["teams"][grp].items():
                        token = data["team_tokens"].get(t_id, "FEHLER")
                        url = f"{base_url}/?token={token}"
                        
                        qr = qrcode.QRCode(version=1, box_size=10, border=4)
                        qr.add_data(url)
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        img_bytes = buf.getvalue()
                        
                        # Generate HTML
                        b64 = base64.b64encode(img_bytes).decode()
                        img_src = f"data:image/png;base64,{b64}"
                        html_content += f\"\"\"
                        <div class="card">
                            <div class="team-name">{t_id} - {t_name}</div>
                            <div class="instruction">Scannt diesen Code, um eure Ergebnisse live einzutragen!</div>
                            <img src="{img_src}" alt="QR Code für {t_name}">
                            <div class="url-text">{url}</div>
                        </div>
                        \"\"\"
                        
                        with qr_cols[idx % 3]:
                            st.write(f"**{t_id} ({t_name})**")
                            st.image(img_bytes, width=150)
                            st.write(f"`{token}`")
                            st.markdown("---")
                        idx += 1
                        
                html_content += "</body></html>"
                
                st.download_button(
                    label="📄 QR-Codes als Druck-Version (.html) herunterladen",
                    data=html_content,
                    file_name="team_qrcodes.html",
                    mime="text/html",
                    type="primary"
                )
            except ImportError:
                st.error("Bitte installiere qrcode und Pillow (pip install qrcode Pillow)")"""

content = content.replace(old_qr_logic, new_qr_logic)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
