"""Search-first Streamlit UI. Styling lives in assets/style.css."""
from html import escape
from time import perf_counter
import pandas as pd
import streamlit as st
from build_index import DATA_DIR, ROOT
from search import parse_filters, search_chat

st.set_page_config(page_title="Group Chat Semantic Search", page_icon="💬", layout="wide")
st.markdown("<style>" + (ROOT / "assets/style.css").read_text(encoding="utf-8-sig") + "</style>",
            unsafe_allow_html=True)


@st.cache_data
def read_chat(modified_at):
    """The modification time invalidates cached CSV data after regeneration."""
    return pd.read_csv(DATA_DIR / "chat.csv", parse_dates=["timestamp"], keep_default_na=False)


def choose_example(text):
    st.session_state["query"] = text
    st.session_state["run_example"] = True


def result_card(result, rank):
    """Escape all chat text before placing it in our static HTML layout."""
    rows = []
    for message in result["context"]:
        matched = message["message_id"] == result["message_id"]
        stamp = pd.Timestamp(message["timestamp"])
        sender = escape(message["sender"])
        badge = '<span class="match-tag">MATCHED MESSAGE</span>' if matched else ""
        rows.append(f"""
<div class="chat-row {'matched' if matched else ''}">
  <div class="avatar" aria-hidden="true">{sender[:1]}</div>
  <div class="chat-content">
    <div class="chat-meta"><span class="chat-name">{sender}</span>
      <time datetime="{stamp.isoformat()}">{stamp:%d %b %Y · %H:%M}</time>{badge}</div>
    <p class="chat-text">{escape(message["text"])}</p>
  </div>
</div>""")
    count = result["occurrences"]
    note = (f"Identical text occurs {count} times within your filters · Showing one occurrence"
            if count > 1 else "Conversation context · Up to 2 messages before and after")
    return f"""
<article class="result-card" aria-label="Search result {rank}">
  <div class="result-top"><span class="result-number">MATCH {rank:02d}</span>
    <span class="similarity">Cosine similarity <strong>{result["score"]:.3f}</strong></span></div>
  <div class="conversation">{''.join(rows)}</div>
  <div class="result-foot">{note}</div>
</article>"""


st.markdown("""
<div class="brandbar">
  <div class="brand"><span class="brandmark" aria-hidden="true">↗</span>groupchat<span style="color:#769178">.</span></div>
  <div class="archive-tag">A little less scrolling</div>
</div>""", unsafe_allow_html=True)

try:
    chat = read_chat((DATA_DIR / "chat.csv").stat().st_mtime_ns)
except FileNotFoundError:
    st.info("The demo chat is not ready yet. Run python generate_chat.py to create it.")
    st.stop()

first, latest = chat.timestamp.min(), chat.timestamp.max()
st.markdown(f"""
<section class="hero">
  <div class="eyebrow">GOOD CONVERSATIONS. EASIER TO FIND.</div>
  <h1>Group Chat<br>Semantic Search</h1>
  <p>Search conversations by meaning, person or time.</p>
  <div class="hero-meta"><span>{len(chat):,} messages</span>
    <span>{chat.sender.nunique()} friends</span><span>{first:%b} – {latest:%b %Y}</span>
    <span>English + Hinglish</span></div>
</section>""", unsafe_allow_html=True)

main, rail = st.columns([3.1, 1.15], gap="large")
with rail:
    people = "".join(
        f'<div class="person"><span class="avatar" aria-hidden="true">{escape(name[:1])}</span>{escape(name)}</div>'
        for name in sorted(chat.sender.unique()))
    st.markdown(f"""
<aside class="rail-card">
  <div class="section-label">THE GROUP</div>
  <div class="group-icon" aria-hidden="true">☏</div>
  <h3>The usual suspects</h3>
  <p>Trips, deadlines, chai breaks.<br>Six months of everyday conversations.</p>
  <div class="people">{people}</div>
  <div class="rail-foot">Synthetic demo conversations.<br>No private WhatsApp chats were imported.</div>
</aside>
<aside class="rail-card tip-card">
  <div class="section-label">A SMALL SEARCH TIP</div>
  <p>Remember the idea, not the wording.<br><br>Try a question in your own words, or add a name and a month to narrow it down.</p>
</aside>""", unsafe_allow_html=True)
    with st.expander("About dates & matches"):
        st.write(f"“Today” is {latest:%d %B %Y}, the latest day in this chat. Last week and last month mean the previous calendar week and month.")
        st.write("Matching text is highlighted with surrounding messages. Identical messages share one result.")
        st.caption("Similarity is not a confidence percentage. English-to-Hinglish questions may miss relevant messages.")

with main:
    st.markdown("""
<div class="section-label">SEARCH THE CONVERSATION</div>
<div class="search-heading">What are you trying to remember?</div>
<div class="search-intro">A plan you made. Something someone said. That one message.</div>
""", unsafe_allow_html=True)
    with st.form("search"):
        st.text_input("Your question", key="query", label_visibility="collapsed",
                      placeholder="When did we decide where to go?")
        submitted = st.form_submit_button("Search conversations  →", type="primary",
                                         use_container_width=True)

    st.caption("Start with an example")
    examples = [
        ("↗  The trip decision", "When did we decide where to go?"),
        ("◎  Priya’s budget", "What did Priya say about our budget?"),
        ("◷  Last month", "What did we discuss last month?"),
    ]
    for column, (label, example) in zip(st.columns(3), examples):
        column.button(label, help=example, on_click=choose_example, args=(example,),
                      use_container_width=True)

    run_example = st.session_state.pop("run_example", False)
    if submitted or run_example:
        query = st.session_state.get("query", "").strip()
        if not query:
            st.session_state.pop("search_result", None)
            st.info("Enter a question to search.")
        else:
            try:
                with st.spinner("Finding your conversation…"):
                    started = perf_counter()
                    results = search_chat(query)
                    sender, start, end = parse_filters(query, chat.sender.unique(), latest)
                st.session_state["search_result"] = {
                    "query": query, "results": results, "sender": sender,
                    "start": start, "end": end, "elapsed": perf_counter() - started,
                }
            except (FileNotFoundError, ValueError, OSError) as error:
                st.session_state.pop("search_result", None)
                st.error("We couldn’t complete that search. Please try again.")
                with st.expander("Setup details"):
                    st.write(str(error))
                    st.caption("Run python build_index.py for a missing or outdated index. The first model download needs internet access.")

    if "search_result" in st.session_state:
        saved = st.session_state["search_result"]
        results = saved["results"]
        st.markdown(f"""
<div class="results-heading"><h2>{len(results)} conversations found</h2><span>{saved["elapsed"]:.1f}s</span></div>
<div class="query-label">Results for “{escape(saved["query"])}”</div>""", unsafe_allow_html=True)
        filters = []
        if saved["sender"]:
            filters.append(f"From {saved['sender']}")
        if saved["start"]:
            last_day = saved["end"] - pd.Timedelta(days=1)
            filters.append(f"{saved['start']:%d %b %Y} – {last_day:%d %b %Y}")
        if filters:
            st.markdown("".join(f'<span class="filter-chip">{escape(f)}</span>' for f in filters),
                        unsafe_allow_html=True)
        if not results:
            st.info("No messages match those filters. Try another person or date.")
        for rank, result in enumerate(results, 1):
            st.markdown(result_card(result, rank), unsafe_allow_html=True)
    else:
        st.markdown("""
<div class="empty-card">
  <div class="empty-symbol" aria-hidden="true">⌕</div>
  <h3>The answer might already be in the chat.</h3>
  <p>Ask a question above to find a message and the conversation around it.<br><br>
  You can ask in Hinglish, too:<br><strong>“kab final hua tha kidhar jana hai?”</strong></p>
</div>""", unsafe_allow_html=True)

st.markdown("""
<div class="footer"><span>Made for the messages you remember almost.</span>
<span>Local chat archive · Synthetic data</span></div>""", unsafe_allow_html=True)
