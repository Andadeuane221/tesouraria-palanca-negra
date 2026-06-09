# 🛡️ Sistema de Tesouraria — Clube de Desbravadores Palanca Negra

O **Palanca Negra Tesouraria** é uma aplicação web leve e intuitiva desenvolvida em Python com Flask e Bootstrap 5. O sistema foi projetado especificamente para gerenciar a arrecadação de fundos, emissão de recibos de pagamento de mensalidades e controle financeiro interno do clube, exibindo métricas em tempo real e operando com a moeda nacional angolana (**AOA**).

---

## 🚀 Funcionalidades Principais

* **Emissão Rápida de Recibos:** Formulário dinâmico com validação de campos obrigatórios.
* **Visualização em Tempo Real:** Conforme você digita os dados no formulário, o espelho do recibo é atualizado instantaneamente na lateral da tela antes mesmo de ser salvo.
* **Painel de Indicadores (Dashboard):**
  * **Total Arrecadado:** Soma histórica de todas as entradas registradas no sistema.
  * **Mês Atual:** Filtragem automatizada que soma apenas os valores arrecadados dentro do mês vigente.
  * **Recibos Emitidos:** Contador total de documentos gerados.
* **Tabela de Histórico Recente:** Exibição imediata dos últimos 10 recibos emitidos diretamente na página inicial.

---

## 💻 Como Usar o Sistema

### 1. Preenchimento de Campos (Emitir Novo Recibo)
O formulário de emissão está dividido em três seções lógicas para evitar erros humanos:

| Seção | Campo | Tipo / Regra | O que preencher? |
| :--- | :--- | :--- | :--- |
| **Dados do Membro** | `Nome Completo da Pessoa` | Obrigatório | O nome do desbravador ou responsável que está efetuando o pagamento. |
| **Pagamento** | `Período de Referência` | Obrigatório | O mês ou trimestre correspondente. *Exemplo: "Janeiro 2026" ou "1º Trimestre".* |
| **Pagamento** | `Valor Pago (AOA)` | Obrigatório | O valor numérico entregue. O sistema formata automaticamente como moeda (`AOA X.XX`). |
| **Administração** | `Nome do Tesoureiro` | Obrigatório | O nome do oficial de tesouraria que está recebendo o valor e assinando o ato. |
| **Administração** | `Departamento Responsável`| Opcional | O departamento de destino do fundo. Padrão: *Tesouraria*. |
| **Administração** | `Observações` | Opcional | Detalhes adicionais sobre o pagamento (Ex: *Referente à parcela do uniforme*). |

### 2. Painel de Indicadores e Filtragem Automatizada
O sistema gerencia os cálculos financeiros de forma transparente, eliminando a necessidade de filtros manuais complexos na tela inicial:
* **Métricas Inteligentes:** O card **"Mês Atual"** utiliza uma consulta direta ao banco de dados utilizando a data e hora do servidor para isolar e somar as transações do mês vigente.
* **Segurança de Dados:** O código de referência (`Ref:`) de cada recibo é gerado por um algoritmo exclusivo do sistema, garantindo autenticidade e impedindo duplicidade de registros.

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3.x e Flask (Microframework)
* **Banco de Dados:** SQLite (Armazenamento em arquivo local integrado `database.db`)
* **Frontend:** HTML5, CSS3, Bootstrap 5 (Estilização e Responsividade) e Bootstrap Icons

---

## 📦 Como Executar o Projeto Localmente

Se você precisar rodar o sistema em ambiente de desenvolvimento no seu computador, certifique-se de ter o Python instalado e execute os passos abaixo no terminal:

```bash
# 1. Clonar o repositório
git clone https://github.com/Andadeuane221/tesouraria-palanca-negra.git
cd tesouraria-palanca-negra.git

# 2. Criar e ativar o ambiente virtual (VENV)
python -m venv venv
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# No Linux/Mac:
source venv/bin/activate

# 3. Instalar as dependências do sistema
pip install -r requirements.txt

# 4. Executar a aplicação
python app.py