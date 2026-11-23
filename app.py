"""Streamlit GUI for the Personal Notes Organizer.

Run with:   streamlit run app.py
"""

from datetime import date

import pandas as pd
import streamlit as st

from notes_organizer import dataio, stats
from notes_organizer.config import build_service
from notes_organizer.errors import NotesError
from notes_organizer.samples import SAMPLE_NOTES
from notes_organizer.service import SORT_OPTIONS

st.set_page_config(page_title="Personal Notes Organizer", page_icon="📝", layout="wide")

PAGES = ["📚 My Notes", "➕ Add Note", "📊 Dashboard", "📥 Import / Export"]


# ---------- small helpers ----------

def flash(kind: str, message: str) -> None:
    """Remember a message to show after the next rerun."""
    st.session_state["flash"] = (kind, message)


def show_flash() -> None:
    kind, message = st.session_state.pop("flash", (None, None))
    if message:
        getattr(st, kind)(message)


def run_action(action, *args, success="Done.", **kwargs):
    """Call a service method and turn errors into friendly messages."""
    try:
        action(*args, **kwargs)
        flash("success", success)
        return True
    except NotesError as err:
        flash("error", str(err))
        return False


# ---------- callbacks (they run before the page redraws) ----------

def start_edit(note_id):
    st.session_state["editing_id"] = note_id
    st.session_state["confirm_delete_id"] = None


def cancel_edit():
    st.session_state["editing_id"] = None


def ask_delete(note_id):
    st.session_state["confirm_delete_id"] = note_id
    st.session_state["editing_id"] = None


def cancel_delete():
    st.session_state["confirm_delete_id"] = None


def do_delete(svc, note_id):
    run_action(svc.delete, note_id, success="Note deleted.")
    st.session_state["confirm_delete_id"] = None


def do_pin(svc, note_id):
    run_action(svc.toggle_pin, note_id, success="Pin updated.")


def load_samples(svc):
    added, _ = svc.add_many(SAMPLE_NOTES)
    flash("success", f"Loaded {added} sample notes.")


# ---------- pages ----------

def page_notes(svc):
    st.header("📚 My Notes")
    all_tags = list(svc.tag_counts().keys())

    top_left, top_mid, top_right = st.columns([3, 3, 2])
    keyword = top_left.text_input("Search", placeholder="title, content or tag...")
    chosen_tags = top_mid.multiselect("Filter by tags", all_tags)
    sort_by = top_right.selectbox("Sort by", SORT_OPTIONS)

    opt_a, opt_b, opt_c = st.columns([2, 2, 4])
    match_all = opt_a.checkbox("Match all tags", help="Note must contain every chosen tag")
    pinned_only = opt_b.checkbox("Pinned only")
    use_dates = opt_c.checkbox("Filter by created date")

    since = until = None
    if use_dates:
        d1, d2 = st.columns(2)
        since = d1.date_input("From", value=date.today().replace(day=1)).isoformat()
        until = d2.date_input("To", value=date.today()).isoformat()

    try:
        notes = svc.search(keyword, chosen_tags, match_all, since, until, pinned_only, sort_by)
    except NotesError as err:
        st.error(str(err))
        return

    st.caption(f"Showing {len(notes)} of {len(svc)} notes")
    if not notes:
        st.info("No notes match. Add one from the sidebar, or load the sample notes.")

    for note in notes:
        label = ("📌 " if note.pinned else "") + note.title
        with st.expander(label):
            if st.session_state.get("editing_id") == note.id:
                edit_form(svc, note)
                continue

            st.markdown(note.content or "_(no content)_")
            st.caption(
                "Tags: " + (", ".join(f"`{t}`" for t in note.tags) or "none")
                + f"  |  Created {note.created_at}  |  Updated {note.updated_at}"
            )

            b1, b2, b3, _ = st.columns([1, 1, 1, 5])
            b1.button("Pin" if not note.pinned else "Unpin", key=f"pin_{note.id}",
                      on_click=do_pin, args=(svc, note.id))
            b2.button("Edit", key=f"edit_{note.id}", on_click=start_edit, args=(note.id,))
            b3.button("Delete", key=f"del_{note.id}", on_click=ask_delete, args=(note.id,))

            if st.session_state.get("confirm_delete_id") == note.id:
                st.warning("Delete this note? This cannot be undone.")
                c1, c2, _ = st.columns([1, 1, 6])
                c1.button("Yes, delete", key=f"yes_{note.id}", type="primary",
                          on_click=do_delete, args=(svc, note.id))
                c2.button("Cancel", key=f"no_{note.id}", on_click=cancel_delete)


def edit_form(svc, note):
    with st.form(f"edit_form_{note.id}"):
        title = st.text_input("Title", value=note.title, max_chars=100)
        content = st.text_area("Content", value=note.content, height=160, max_chars=10000)
        tags = st.text_input("Tags (comma separated)", value=", ".join(note.tags))
        save, cancel = st.columns([1, 1])
        saved = save.form_submit_button("Save changes", type="primary")
        cancelled = cancel.form_submit_button("Cancel")

    if cancelled:
        cancel_edit()
        st.rerun()
    if saved:
        if run_action(svc.update, note.id, title=title, content=content, tags=tags,
                      success="Note updated."):
            cancel_edit()
        st.rerun()


def page_add(svc):
    st.header("➕ Add a note")
    with st.form("add_form", clear_on_submit=True):
        title = st.text_input("Title", max_chars=100)
        content = st.text_area("Content", height=200, max_chars=10000)
        tags = st.text_input("Tags (comma separated)", placeholder="exam, physics")
        pinned = st.checkbox("Pin this note")
        submitted = st.form_submit_button("Save note", type="primary")

    if submitted:
        try:
            note = svc.add(title, content, tags, pinned)
            st.success(f"Saved note #{note.id}: {note.title}")
        except NotesError as err:
            st.error(str(err))


def page_dashboard(svc):
    st.header("📊 Dashboard")
    notes = svc.list_notes()
    info = stats.summary(notes)

    cols = st.columns(5)
    cols[0].metric("Notes", info["total_notes"])
    cols[1].metric("Pinned", info["pinned_notes"])
    cols[2].metric("Tags", info["unique_tags"])
    cols[3].metric("Words", info["total_words"])
    cols[4].metric("Untagged", info["untagged_notes"])

    left, right = st.columns(2)
    with left:
        st.subheader("Notes per tag")
        counts = svc.tag_counts()
        if counts:
            st.bar_chart(pd.DataFrame({"notes": list(counts.values())}, index=list(counts.keys())))
        else:
            st.caption("No tags yet.")
    with right:
        st.subheader("Created in the last 7 days")
        per_day = stats.notes_per_day(notes)
        st.bar_chart(pd.DataFrame({"notes": list(per_day.values())}, index=list(per_day.keys())))


def page_import_export(svc):
    st.header("📥 Import / Export")

    st.subheader("Export")
    notes = svc.list_notes("oldest")
    c1, c2 = st.columns(2)
    c1.download_button("Download as CSV", dataio.notes_to_csv(notes),
                       file_name="notes.csv", mime="text/csv")
    c2.download_button("Download as JSON", dataio.notes_to_json(notes),
                       file_name="notes.json", mime="application/json")

    st.divider()
    st.subheader("Import")
    uploaded = st.file_uploader("Choose a .csv or .json file", type=["csv", "json"])
    if uploaded is not None and st.button("Import notes", type="primary"):
        try:
            text = uploaded.getvalue().decode("utf-8-sig")
            items = dataio.parse_file_text(text, uploaded.name)
            added, skipped = svc.add_many(items)
            st.success(f"Imported {added} note(s). Skipped {len(skipped)}.")
            for message in skipped[:10]:
                st.warning(message)
        except UnicodeDecodeError:
            st.error("That file is not UTF-8 text.")
        except NotesError as err:
            st.error(str(err))


# ---------- main ----------

def main():
    try:
        svc = build_service()
    except NotesError as err:
        st.error(f"Could not open the notes file: {err}")
        st.stop()

    st.session_state.setdefault("editing_id", None)
    st.session_state.setdefault("confirm_delete_id", None)

    with st.sidebar:
        st.title("📝 Notes Organizer")
        page = st.radio("Go to", PAGES, label_visibility="collapsed")
        st.caption(f"{len(svc)} notes stored")
        if len(svc) == 0:
            st.button("Load sample notes", on_click=load_samples, args=(svc,))
        st.caption("StudentLife Hack - Project #102")

    show_flash()

    if page == PAGES[0]:
        page_notes(svc)
    elif page == PAGES[1]:
        page_add(svc)
    elif page == PAGES[2]:
        page_dashboard(svc)
    else:
        page_import_export(svc)


main()
