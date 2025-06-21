import openai

def generate_daily_report(entries, openai_api_key):
    openai.api_key = openai_api_key

    prompt = "以下は1日の作業記録です。これをもとに300文字以内の自然な業務日報を作成してください：\n"
    for start, end, title in entries:
        prompt += f"- {start}〜{end}：{title}\n"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
