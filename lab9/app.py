from flask import Flask, request, render_template, jsonify
from ftplib import FTP
import smtplib
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('page.html')


@app.route('/upload', methods=['POST'])
def upload_file_ftp():
    try:
        hostname = '138.68.98.108'
        username = 'yourusername'
        password = 'yourusername'

        file = request.files['file']
        filename = secure_filename(file.filename)

        ftp = FTP(hostname)
        ftp.login(user=username, passwd=password)

        ftp.cwd('faf-212')

        working_directory = 'lesenco'
        if working_directory not in ftp.nlst():
            ftp.mkd(working_directory)

        ftp.cwd(working_directory)
        wb = ftp.pwd()

        in_memory_file = BytesIO()
        file.save(in_memory_file)
        in_memory_file.seek(0)

        ftp.storbinary(f'STOR {filename}', in_memory_file)

        ftp.quit()

        file_url = f"ftp://{username}:{password}@{hostname}/{wb}/{filename}"

        if send_email(file_url):
            return render_template('success.html', file_url=file_url)

    except Exception as e:
        print(f"File upload failed. Error: {str(e)}")

    return render_template('error.html'), 500


def send_email(file_url):
    subject = request.form.get('subject')
    body = request.form.get('body')
    sender = 'leshenko.mri@gmail.com'
    password = 'rkpj pwdk wwtg ivnk'
    recipient_email = request.form.get('recipientEmail')

    body_with_url = f"{body}\n\nFile URL: {file_url}"

    msg = MIMEText(body_with_url)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, password)
            smtp_server.sendmail(sender, recipient_email, msg.as_string())
            return True

    except Exception as e:
        print(f"Email sending failed. Error: {str(e)}")
        return False


if __name__ == '__main__':
    app.run(debug=True)
