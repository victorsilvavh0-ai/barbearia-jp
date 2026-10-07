from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

app = Flask(__name__)
app.secret_key = 'barbearia_jp_secret_key'

def init_db():
    conn = sqlite3.connect('barbearia.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            UNIQUE(data, horario)
        )
    ''')
    conn.commit()
    conn.close()

def gerar_horarios_dia():
    horarios = []
    inicio = datetime.strptime("09:00", "%H:%M")
    fim = datetime.strptime("21:40", "%H:%M")
    duracao = timedelta(minutes=40)

    atual = inicio
    while atual + duracao <= fim:
        horarios.append(atual.strftime("%H:%M"))
        atual += duracao
    return horarios

@app.route('/', methods=['GET', 'POST'])
def index():
    todos_horarios = gerar_horarios_dia()
    data_selecionada = request.args.get('data', datetime.today().strftime('%Y-%m-%d'))
    link_whatsapp = request.args.get('link_whatsapp', None)

    conn = sqlite3.connect('barbearia.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        data = request.form.get('data')
        horario = request.form.get('horario')


# Se for domingo, impede o envio
        if datetime.strptime(data, "%Y-%m-%d").weekday() == 6:
            flash('Não realizamos agendamentos aos domingos.', 'danger')
            conn.close()
            return redirect(url_for('index', data=data))

        try:
            cursor.execute(
                'INSERT INTO agendamentos (cliente_nome, telefone, data, horario) VALUES (?, ?, ?, ?)',
                (nome, telefone, data, horario)
            )
            conn.commit()
            
            # Número do WhatsApp da Barbearia do JP (DDD + NUMERO)
            numero_barbearia = "5532984203114"  # Substitua pelo número real do JP

            # Formatar a data para DD/MM/AAAA
            data_formatada = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")

            # Texto automático da mensagem
            mensagem = f"Olá, JP! Meu nome é *{nome}*. Acabei de agendar um horário para o dia *{data_formatada}* às *{horario}*."
            mensagem_codificada = urllib.parse.quote(mensagem)

            # Link do WhatsApp
            link_whatsapp = f"https://api.whatsapp.com/send?phone={numero_barbearia}&text={mensagem_codificada}"

            flash('Agendamento realizado com sucesso!', 'success')
            conn.close()
            return redirect(url_for('index', data=data, link_whatsapp=link_whatsapp))

        except sqlite3.IntegrityError:
            flash('Este horário acabou de ser preenchido por outro cliente. Escolha outro.', 'danger')
            conn.close()
            return redirect(url_for('index', data=data))

    cursor.execute('SELECT horario FROM agendamentos WHERE data = ?', (data_selecionada,))
    ocupados = [row[0] for row in cursor.fetchall()]
    conn.close()

    horarios_livres = [h for h in todos_horarios if h not in ocupados]

    return render_template(
        'index.html',
        horarios=horarios_livres,
        data_selecionada=data_selecionada,
        hoje=datetime.today().strftime('%Y-%m-%d'),
        link_whatsapp=link_whatsapp
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)