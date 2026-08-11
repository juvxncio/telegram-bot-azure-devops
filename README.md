# 🤖 Telegram Bot - Azure DevOps Reports

Bot do Telegram para gerar relatórios de **horas trabalhadas** e **tarefas concluídas** diretamente a partir do **Azure DevOps**.  
Permite que uma equipe acompanhe a produtividade via comandos no Telegram.

---

## 🚀 Funcionalidades
- `/start` → Menu com opções dos comandos abaixo.
- `/horas [mês] [ano]` → Relatório de horas trabalhadas por pessoa no período.
- `/descricao task [mês] [ano]` → Relatório de tarefas concluídas no período sem descrição/com descrição padrão.
- `/descricao bug [mês] [ano]` → Relatório de bugs concluídos no período sem descrição/com descrição padrão.
- `/descricao historia [mês] [ano]` → Relatório de histórias concluídas no período sem descrição ou critérios de aceite/com descrição ou critérios de aceite padrão.
- `/done [mês] [ano]` → Relatório de histórias cujo status Done tenha sido feito por alguém não autorizado.
- `/completo [mês] [ano]` → Junção dos comandos anteriores em um só relatório.
- `/transbordo [mês] [ano]` → Relatório de histórias que foram movidas de sprint.
- `/id` → Mostra o seu ID de usuário e o Chat ID (útil para configurar permissões).
- Relatórios grandes são enviados automaticamente como arquivo `.txt`.

---

## 🛠️ Pré-requisitos
- Python 3.10+  
- Conta no **Azure DevOps** com acesso às APIs  
- Bot do Telegram (criado via **BotFather**)  
- **venv** para dependências isoladas (ou **Docker**, veja a seção "Executando com Docker" abaixo)

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

Para rodar testes ou usar ferramentas de lint/formatação (black, blue, flake8, pytest), instale também as dependências de desenvolvimento — `requirements-dev.txt` já inclui `requirements.txt`:

```bash
pip install -r requirements-dev.txt
```

Copie `.env.example` para `.env` e preencha com seus valores:

```bash
cp .env.example .env
```

```env
PAT=SEU_PAT_AQUI
URL_BASE=https://dev.azure.com/ORGANIZAÇÃO/
lista_times_ignorados=LISTA_COM_TIMES_A_SEREM_IGNORADOS
TELEGRAM_TOKEN=SEU_TOKEN_AQUI
GRUPO_PERMITIDO=ID_DO_GRUPO_OU_USUARIO_TELEGRAM
TEMPLATE_PADRAO_TASK=1
TEMPLATE_PADRAO_PBI=1
TEMPLATE_PADRAO_BUG=1
TEMPLATE_PADRAO_CRITERIOS_DE_ACEITE=1
DOMINIO_AUTORIZADO_DONE=@dominio.autorizado.com
```

> 🔑 O `GRUPO_PERMITIDO` é o chat ID onde os comandos podem ser executados — inclusive o menu de botões do `/start`.  
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

Pra parar o bot: `Ctrl+C`. Depois de editar o `.env`, pare e rode de novo — as variáveis só são lidas na inicialização.

---

## 🐳 Executando com Docker

Alternativa ao venv, com ambiente isolado e reproduzível:

```bash
docker build -t telegram-bot-azure-devops .
docker run --rm --env-file .env telegram-bot-azure-devops
```

O `.env` é passado em tempo de execução (`--env-file`), nunca copiado pra dentro da imagem.

> ⚠️ O Telegram só permite **uma instância** fazendo polling por token ao mesmo tempo. Se o bot já estiver rodando via venv, pare-o (`Ctrl+C`) antes de subir o container — senão as duas instâncias vão brigar pelo `getUpdates` (erro `Conflict`).

---

## 🧪 Testes

O projeto usa [pytest](https://pytest.org). Com as dependências de desenvolvimento instaladas (`pip install -r requirements-dev.txt`):

```bash
pytest
```

Os testes cobrem as funções puras do projeto (cálculo de horas úteis, cálculo de mês/ano padrão, autorização de chat) e regressões de bugs já corrigidos — não fazem chamadas reais ao Azure DevOps ou Telegram. CI no GitHub Actions ([.github/workflows/tests.yml](.github/workflows/tests.yml)) roda a suíte a cada push/PR nas branches `main` e `dev`.

---

## 📂 Estrutura do projeto

```
telegram-bot-azure-devops/
│
├── api/
│   ├── __init__.py
│   ├── azure.py          # Integração com Azure DevOps
│   └── relatorios.py     # Geração de relatórios
│
├── bot/
│   ├── __init__.py
│   ├── handlers.py       # Handlers dos comandos do bot
│   └── main.py           # Inicialização do bot
│
├── utils/
│   ├── __init__.py
│   └── datas.py          # Funções auxiliares de datas/horas
│
├── tests/                # Testes automatizados (pytest)
│
├── .github/workflows/    # CI (roda os testes a cada push/PR)
│
├── .env                  # Variáveis de ambiente (não versionar)
├── .env.example          # Modelo de .env pra copiar
├── Dockerfile            # Build da imagem do bot
├── requirements.txt      # Dependências de runtime
├── requirements-dev.txt  # + testes e lint (herda requirements.txt)
└── README.md             # Este guia
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
