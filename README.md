Este aplicativo foi criado por Rodolf Gouveia. GitHub: [@Andadeuane221](https://github.com/Andadeuane221)

# 🛡️ Sistema de Tesouraria — Clube de Desbravadores Palanca Negra

O **Palanca Negra Tesouraria** é uma aplicação web robusta, leve e segura desenvolvida em Python com Flask, SQLite e Bootstrap 5. O sistema foi projetado especificamente para gerenciar a arrecadação de fundos, controle de acesso administrativo por login, exportação de relatórios avançados e emissão de recibos profissionais em PDF para o controle financeiro interno do clube, operando com a moeda nacional angolana (**AOA**).

---

## 🚀 Funcionalidades Principais

* **Autenticação de Segurança (Novo):** Acesso restrito ao painel por meio de login. As senhas são protegidas no banco de dados utilizando criptografia de alta segurança (*hash* via Werkzeug).
* **Emissão Rápida de Recibos:** Formulário dinâmico com validações automáticas de integridade de dados.
* **Código de Referência Inteligente (Atualizado):** Cada recibo gera uma chave única padronizada em `AAAAMMDD-HHMMSS-NOMEDOMEMBRO`. O nome do tesoureiro foi removido do código para manter a referência limpa, curta e profissional.
* **Geração de PDFs Profissionais (Novo):** Emissão e download instantâneo de recibos com layout corporativo A4 construídos de forma nativa com a biblioteca ReportLab.
* **Exportação de Dados Avançada (Novo):** Download do histórico completo de arrecadações para fechamentos contabilísticos nos formatos **Excel (.xlsx)** e **CSV**.
* **Histórico com Pesquisa e Paginação (Novo):** Área exclusiva para listagem de recibos com filtros dinâmicos por texto (busca por membro, referência ou tesoureiro) e filtros por mês de emissão, divididos em páginas de 10 registros.
* **Painel de Indicadores (Dashboard):**
* **Total Arrecadado:** Soma histórica de todas as entradas registradas no sistema.
* **Mês Atual:** Filtragem automatizada que isola e soma apenas os valores arrecadados dentro do mês vigente.
* **Recibos Emitidos:** Contador total de documentos gerados no sistema.



---

## 💻 Como Usar o Sistema

### 1. Preenchimento de Campos (Emitir Novo Recibo)

O formulário de emissão está estruturado para evitar erros humanos:

| Seção | Campo | Tipo / Regra | O que preencher? |
| --- | --- | --- | --- |
| **Dados do Membro** | `Nome Completo da Pessoa` | Obrigatório | O nome do desbravador ou responsável que está efetuando o pagamento. |
| **Pagamento** | `Período de Referência` | Obrigatório | O mês ou trimestre correspondente. *Exemplo: "Janeiro 2026" ou "1º Trimestre".* |
| **Pagamento** | `Valor Pago (AOA)` | Obrigatório | O valor numérico entregue. O sistema formata automaticamente como moeda (`AOA X.XX`). |
| **Administração** | `Nome do Tesoureiro` | Obrigatório | O nome do oficial de tesouraria que está recebendo o valor e assinando o ato. |
| **Administração** | `Departamento Responsável` | Opcional | O departamento de destino do fundo. Padrão: *Tesouraria*. |
| **Administração** | `Observações` | Opcional | Detalhes adicionais sobre o pagamento (Ex: *Referente à parcela do uniforme*). |

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3.x e Flask (Microframework)
* **Segurança:** Werkzeug Security (Algoritmos de Criptografia pbkdf2:sha256)
* **Geração de Relatórios:** ReportLab (Geração de PDFs)
* **Manipulação de Dados:** Pandas e Openpyxl (Exportação Excel/CSV)
* **Banco de Dados:** SQLite (Arquivo local integrado `database.db`)
* **Frontend:** HTML5, CSS3, Bootstrap 5 e Bootstrap Icons

---

## 📦 Como Executar o Projeto Localmente

Se você precisar rodar o sistema em ambiente de desenvolvimento no seu computador, certifique-se de ter o Python instalado e execute os passos abaixo no terminal:

### 1. Clonar o repositório

```bash
git clone https://github.com/Andadeuane221/tesouraria-palanca-negra.git
cd tesouraria-palanca-negra

```

### 2. Criar e ativar o ambiente virtual (VENV)

* **No Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

```


* **No Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate

```



### 3. Instalar as dependências do sistema

```bash
pip install flask reportlab pandas openpyxl werkzeug

```

### 4. Configurar o Usuário de Acesso (Obrigatório)

Por motivos de segurança, as senhas não ficam escritas diretamente no código. Antes de ligar o servidor, execute o gerador interativo para criar o seu usuário no banco de dados local:

```bash
python gerar_acesso.py

```

*Insira o nome de usuário desejado e a sua senha secreta no terminal.*

### 5. Executar a aplicação

```bash
python app.py

```

O sistema estará pronto e operando no endereço local: `http://127.0.0.1:5000/`

---

## 🔐 Segurança em Produção

* O arquivo `gerar_acesso.py` foi adicionado ao `.gitignore` para garantir que scripts locais com interações de credenciais nunca sejam vazados para o GitHub.
* Ao realizar o deploy em servidores de produção (como o *PythonAnywhere*), execute o script `gerar_acesso.py` diretamente dentro do console Bash do servidor para criar o acesso oficial de forma 100% protegida e privada.