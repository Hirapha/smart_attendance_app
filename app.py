import streamlit as st
from datetime import datetime, date
from utils.db import *
from utils.report import generate_daily_report
from utils.auth import init_user_db, verify_user, add_user
from openpyxl import load_workbook
from io import BytesIO

init_user_db()
init_db()
today = date.today().isoformat()
st.set_page_config(page_title="スマート勤怠", layout="wide")

# セッション管理
if "last_time" not in st.session_state:
    st.session_state.last_time = None

st.title("📲 スマート勤怠アプリ")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 追加：モード切り替えフラグ
if "input_mode" not in st.session_state:
    st.session_state.input_mode = False


if not st.session_state.authenticated:
    st.title("🔐 勤怠アプリ")

    tabs = st.tabs(["ログイン", "新規登録"])

    with tabs[0]:  # 🔐 ログイン
        st.subheader("ログイン")
        username = st.text_input("ユーザー名", key="login_user")
        password = st.text_input("パスワード", type="password", key="login_pass")

        if st.button("ログイン"):
            if verify_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("ログイン成功！")
                st.rerun()
            else:
                st.error("ユーザー名またはパスワードが違います。")

    with tabs[1]:  # 🆕 新規登録
        st.subheader("新規ユーザー登録")
        new_username = st.text_input("新しいユーザー名", key="new_user")
        new_password = st.text_input("パスワード", type="password", key="new_pass")
        confirm = st.text_input("パスワード確認", type="password", key="confirm_pass")

        if st.button("登録する"):
            if not new_username or not new_password:
                st.warning("ユーザー名とパスワードを入力してください。")
            elif new_password != confirm:
                st.warning("パスワードが一致しません。")
            elif verify_user(new_username, new_password):
                st.error("このユーザー名はすでに使われています。")
            else:
                add_user(new_username, new_password)
                st.success("登録完了！ログインタブからログインしてください。")

    st.stop()



# セッション初期化
if "last_time" not in st.session_state:
    st.session_state.last_time = None
if "pending_entry" not in st.session_state:
    st.session_state.pending_entry = None

# -----------------------
# 打刻処理
# -----------------------
if st.button("🔘 打刻") and not st.session_state.input_mode:
    now = datetime.now()
    if st.session_state.last_time:
        st.session_state.pending_entry = {
            "start": st.session_state.last_time,
            "end": now
        }
        st.session_state.last_time = now
        st.session_state.input_mode = True  # 入力欄を表示する
        st.session_state.last_time = None
    else:
        st.session_state.last_time = now
        st.info(f"開始時刻を記録しました：{now.strftime('%H:%M')}")

if st.session_state.input_mode and st.session_state.pending_entry:
    entry = st.session_state.pending_entry
    st.success(f"作業：{entry['start'].strftime('%H:%M')} ～ {entry['end'].strftime('%H:%M')}")
    title = st.text_input("作業タイトル", key="title_input")
    memo = st.text_area("メモ（任意）", key="memo_input")

    if st.button("✅ 作業を保存"):
        insert_entry(
            username=st.session_state.username,
            date=entry['start'].date().isoformat(),
            start=entry['start'].strftime("%H:%M"),
            end=entry['end'].strftime("%H:%M"),
            title=title,
            memo=memo
        )
        st.success("保存完了しました！")
        st.session_state.pending_entry = None
        st.session_state.input_mode = False  # 入力欄を閉じる


st.divider()

st.header("📅 カレンダーから記録を見る")

# ユーザーが過去の日付を選択できるようにする
selected_date = st.date_input("日付を選択", value=date.today())

# 選択された日付の作業履歴を表示
st.header(f"📖 {selected_date.strftime('%Y-%m-%d')} の作業履歴")
entries = get_entries_by_date(st.session_state.username, selected_date.isoformat())

if entries:
    for entry in entries:
        entry_id, start, end, title, memo = entry
        with st.expander(f"🕒 {start}〜{end}｜📌 {title}"):
            new_title = st.text_input("作業タイトル", value=title, key=f"title_{entry_id}")
            new_memo = st.text_area("メモ", value=memo, key=f"memo_{entry_id}")

            from datetime import datetime
            start_time_obj = datetime.strptime(start, "%H:%M").time()
            end_time_obj = datetime.strptime(end, "%H:%M").time()

            new_start = st.time_input("開始時刻", value=start_time_obj, key=f"start_{entry_id}", step=60)
            new_end = st.time_input("終了時刻", value=end_time_obj, key=f"end_{entry_id}", step=60)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ 編集", key=f"edit_{entry_id}"):
                    update_entry(
                        entry_id=entry_id,
                        start=new_start.strftime("%H:%M"),
                        end=new_end.strftime("%H:%M"),
                        title=new_title,
                        memo=new_memo
                    )
                    st.success("更新しました！")
                    st.rerun()
            with col2:
                if st.button("🗑️ 削除", key=f"delete_{entry_id}"):
                    delete_entry(entry_id)
                    st.warning("削除しました！")
                    st.rerun()
else:
    st.info("この日にはまだ作業記録がありません。")

st.header("📤 請求書を自動生成")
task_label = st.text_input("全体の作業タイトル", value="例) 通常業務")
this_year = date.today().year
this_month = date.today().month
year = st.selectbox("年", list(range(this_year - 2, this_year + 2)), index=2)
month = st.selectbox("月", list(range(1, 13)), index=this_month - 1)
target_month = f"{year}-{month:02d}"
unit_price = st.number_input("時間給（円）", min_value=0, step=100, value=3000)

if st.button("📥 請求書を生成"):
    entries = get_entries_by_month(st.session_state.username, target_month)  # ← utils.db 側に追加が必要
    monthly_total_hours = sum(sum(e['duration'] for e in v) for v in entries.values()) / 60
    wb = load_workbook("invoice_template.xlsx")
    invoice_ws = wb["請求書"]
    report_ws = wb["稼働時間報告書（時間単価の場合提出）"]

    for date_str, tasks in entries.items():
        day = int(date_str.split("-")[2])
        row = day + 6
        task_lines = [f"- {t['title']}（{t['duration']/60:.1f}h）" for t in tasks]
        total_hours = sum(t['duration'] for t in tasks) / 60
        report_ws[f"D{row}"] = "\n".join(task_lines)
        report_ws[f"C{row}"] = total_hours

    report_ws["C38"] = monthly_total_hours
    invoice_ws["C25"] = task_label
    invoice_ws["I25"] = unit_price
    invoice_ws["K26"] = unit_price * monthly_total_hours
    invoice_ws["I26"] = invoice_ws["K26"].value * 1.1

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"請求書_{target_month.replace('-', '')}.xlsx"
    st.download_button("📤 ダウンロード", data=output, file_name=filename,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
