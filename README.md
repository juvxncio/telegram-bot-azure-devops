# 🤖 Telegram Bot - Azure DevOps Reports

Bot do Telegram para gerar relatórios de **horas trabalhadas** e **tarefas concluídas** diretamente a partir do **Azure DevOps**.  
Permite que uma equipe acompanhe a produtividade via comandos no Telegram.

---

## 🚀 Funcionalidades
- `/horas [mês] [ano]` → Relatório de horas trabalhadas por pessoa no período.
- `/descricao task [mês] [ano]` → Relatório de tarefas concluídas no período sem descrição/com descrição padrão.
- `/descricao bug [mês] [ano]` → Relatório de bugs concluídos no período sem descrição/com descrição padrão.
- `/descricao historia [mês] [ano]` → Relatório de histórias concluídas no período sem descrição ou critérios de aceite/com descrição ou critérios de aceite padrão.
- `/done [mês] [ano]` → Relatório de histórias cujo status Done tenha sido feito por alguém não autorizado.
- `/transbordo [mês] [ano]` → Relatório de histórias que foram movidas de sprint.
- `/completo [mês] [ano]` → Junção dos comandos anteriores em um só relatório.
- `/id` → Mostra o seu ID de usuário e o Chat ID (útil para configurar permissões).
- Relatórios grandes são enviados automaticamente como arquivo `.txt`.

---

## 🛠️ Pré-requisitos
- Python 3.10+  
- Conta no **Azure DevOps** com acesso às APIs  
- Bot do Telegram (criado via **BotFather**)  
- **venv** para dependências isoladas  

---

## 🤖 Criando o bot no BotFather
1. Abra o Telegram e procure pelo contato `@BotFather`.
2. Digite o comando:
   ```
   /newbot
   ```
3. Informe o **nome do bot** (ex.: `Azure DevOps Reports Bot`).
4. Informe o **username** (precisa terminar com `bot`, ex.: `azure_devops_bot`).
5. O BotFather retornará uma mensagem com o **Token de API**:
   ```
   Use this token to access the HTTP API:
   1234567890:ABCdefGhIJKlmNoPQRstuVWXyz
   ```
6. Copie esse token e salve no arquivo `.env`.

---

## 🔑 Criando o PAT no Azure DevOps

1. Acesse sua conta do Azure DevOps.
2. Clique na sua foto de perfil no canto superior direito e selecione Security.
3. Vá em Personal Access Tokens e clique em New Token.
4. Configure:
   ```
   Name: Nome do token
   Organization: Sua organização
   Expiration: Defina conforme necessidade
   Scopes: Work Items (Read) e Project and Team (Read)
   ```
5. Clique em Create e copie o token gerado.
6. Copie esse token e salve no arquivo `.env`.

## ⚙️ Configuração do projeto

Clone este repositório e entre na pasta:

```bash
git clone https://github.com/seu-usuario/telegram-bot-azure-devops.git
cd telegram-bot-azure-devops
```

Crie o ambiente virtual e instale as dependências:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto:

```env
PAT=SEU_PAT_AQUI
URL_BASE=https://dev.azure.com/ORGANIZAÇÃO/
lista_times_ignorados=LISTA_COM_TIMES_A_SEREM_IGNORADOS
TELEGRAM_TOKEN=SEU_TOKEN_AQUI
GRUPO_PERMITIDO=ID_DO_GRUPO_OU_USUARIO_TELEGRAM
TEMPLATE_PADRAO_TASK=1
TEMPLATE_PADRAO_PBI=1
TEMPLATE_PADRAO_BUG=1
TEMPLATE_PADRAO_CRITERIO_DE_ACEITE=1
```

> 🔑 O `GRUPO_PERMITIDO` é o chat ID onde os comandos podem ser executados.  
> Você pode descobrir usando o comando `/id` no bot.

---

## ▶️ Executando o bot

Sempre rode da raiz do projeto:

```bash
python3 -m bot.main
```

Você verá no terminal:
```
Bot iniciado. Aguardando comandos...
```

Agora basta abrir o Telegram e enviar comandos ao seu bot 🚀

---

## 📂 Estrutura do projeto

```
telegram-bot-azure-devops/
│
├── api/
│   ├── __init__.py
│   ├── azure.py        # Integração com Azure DevOps
│   └── relatorios.py   # Geração de relatórios
│
├── bot/
│   ├── __init__.py
│   ├── handlers.py     # Handlers dos comandos do bot
│   └── main.py         # Inicialização do bot
│
├── utils/
│   ├── __init__.py
│   └── datas.py        # Funções auxiliares de datas/horas
│
├── .env                # Variáveis de ambiente (não versionar)
├── requirements.txt    # Dependências do projeto
└── README.md           # Este guia
```

---

## 📦 Dependências principais
- [python-telegram-bot](https://python-telegram-bot.org/) → interação com o Telegram  
- [requests](https://pypi.org/project/requests/) → chamadas à API do Azure DevOps  
- [python-dotenv](https://pypi.org/project/python-dotenv/) → variáveis de ambiente  
- [babel](https://babel.pocoo.org/) → formatação de datas  

---

## 📌 Observações
- Apenas o **chat autorizado** (ID definido no `.env`) pode executar comandos.  
- Se o relatório ultrapassar 4000 caracteres, ele será enviado como arquivo `.txt`.  
- O projeto pode ser facilmente estendido para outros comandos (ex.: relatórios de sprint, bugs abertos etc.).

---

## 📜 Licença
Este projeto é livre para uso pessoal ou em equipe. Modifique conforme necessário 🚀
