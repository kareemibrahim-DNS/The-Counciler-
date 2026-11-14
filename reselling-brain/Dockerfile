# Reselling Brain Slack bot (Socket Mode: no public URL needed).
# Build context = this folder (reselling-brain/), so the bot gets knowledge/ and catalog/ next to slack-bot/.
FROM python:3.12-slim
WORKDIR /app
COPY slack-bot/requirements.txt slack-bot/requirements.txt
RUN pip install --no-cache-dir -r slack-bot/requirements.txt
COPY knowledge knowledge
COPY catalog catalog
COPY slack-bot slack-bot
WORKDIR /app/slack-bot
# Fail the build if the offline tests (layers, partner-channel gate, catalogue) don't pass.
RUN python -m unittest test_brain
CMD ["python", "app.py"]
