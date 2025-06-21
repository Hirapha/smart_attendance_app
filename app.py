import streamlit as st
from datetime import datetime, date
from utils.db import *
from utils.report import generate_daily_report
from utils.auth import init_user_db, verify_user, add_user
from openpyxl import load_workbook
from io import BytesIO
import math


init_user_db()
init_db()
init_pending_log_table()
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
                st.session_state.just_logged_in = True
                if "just_logged_in" in st.session_state and st.session_state.just_logged_in:
                    st.session_state.last_time = get_pending_start(st.session_state.username)
                    st.session_state.just_logged_in = False
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
            elif user_exists(new_username):
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
if st.session_state.last_time:
    st.info(f"開始時刻を記録しました：{st.session_state.last_time.strftime('%H:%M')}")
if st.button("🔘 打刻") and not st.session_state.input_mode:
    now = datetime.now()
    pending_start = get_pending_start(st.session_state.username)
    if pending_start:
        st.session_state.pending_entry = {
            "start": st.session_state.last_time,
            "end": now
        }
        clear_pending_start(st.session_state.username)
        st.session_state.input_mode = True  # 入力欄を表示する
        st.session_state.last_time = None
    else:
        st.session_state.last_time = now
        save_pending_start(st.session_state.username, now.isoformat())
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

uploaded_file = st.file_uploader("請求書テンプレートをアップロード", type=["xlsx"])
if uploaded_file is not None:
    wb = load_workbook(uploaded_file)

task_label = st.text_input("全体の作業タイトル", value="例) 通常業務")
this_year = date.today().year
this_month = date.today().month
year = st.selectbox("年", list(range(this_year - 2, this_year + 2)), index=2)
month = st.selectbox("月", list(range(1, 13)), index=this_month - 1)
target_month = f"{year}-{month:02d}"
unit_price = st.number_input("時間給（円）", min_value=0, step=100, value=3000)

if st.button("📥 請求書を生成"):
    if uploaded_file is None:
        st.info("アップロードされたファイルはありません")
    else:
        entries = get_entries_by_month(st.session_state.username, target_month)  # ← utils.db 側に追加が必要
        monthly_total_hours = sum(sum(e['duration'] for e in v) for v in entries.values()) / 60
        invoice_ws = wb["請求書"]
        report_ws = wb["稼働時間報告書（時間単価の場合提出）"]

        for date_str, tasks in entries.items():
            day = int(date_str.split("-")[2])
            row = day + 6

            task_lines = [f"- {t['title']}（{math.floor(t['duration'] / 6) / 10:.1f}h）" for t in tasks]
            total_hours = sum(t['duration'] for t in tasks) / 60
            total_hours = math.floor(total_hours * 10) / 10  # 小数点第2位以下を切り捨て

            report_ws[f"D{row}"] = "\n".join(task_lines)
            report_ws[f"C{row}"] = total_hours

        # 月全体の合計時間（小数点第2位以下切り捨て）
        monthly_total_hours = math.floor(monthly_total_hours * 10) / 10
        report_ws["C38"] = monthly_total_hours

        # 請求書シート
        invoice_ws["C25"] = task_label
        invoice_ws["I25"] = unit_price
        invoice_ws["G25"] = total_hours

        subtotal = unit_price * monthly_total_hours
        subtotal = math.floor(subtotal * 10) / 10
        invoice_ws["K26"] = subtotal

        tax_included = math.floor(subtotal * 11) / 10
        invoice_ws["J26"] = tax_included
        invoice_ws["D16"] = f"{year}年　{month+2}月　1日"
        invoice_ws["I4"] = f"発行日：{year}年　{month}月　{date.today().day}日"


        output = BytesIO()
        wb.save(output)
        output.seek(0)
        filename = f"請求書_{target_month.replace('-', '')}.xlsx"
        st.download_button("📤 ダウンロード", data=output, file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
