services:
  - type: worker
    name: pm-blocker-bot
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: API_ID
        sync: false
      - key: API_HASH
        sync: false
      - key: PHONE
        sync: false
      - key: SUPPORT_BOT_TOKEN
        sync: false
      - key: SUPPORT_BOT_USERNAME
        value: @chatbot11011_bot
      - key: WHITELIST_IDS
        sync: false
