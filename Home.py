import streamlit as st
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# streamlit run Home.py
# Weight ÷ ( 1.0278 - ( 0.0278 × Number of repetitions ) ) - 1RM formula, can be adapted.


def sync_sheet():
    '''
    Gets updated google sheets data.
    '''
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.session_state['df'] = conn.read(worksheet='Data', ttl=1)
    st.session_state['exercises'] = conn.read(
        worksheet='Exercises', ttl=1)


def signed_in():
    '''
    Returns Boolean
    '''
    return 'name' in st.session_state


def signed_in_checkmark():
    '''
    Returns Emoji.
    '''
    if signed_in():
        return '✅'
    return '❌'


def push_data(entry):
    '''
    Adds missing columns to 'entry' DataFrame, downloads up to date Sheet, Merges the two and then reuploads.
    '''
    entry.insert(0, 'Timestamp', [datetime.now().strftime(
        "%Y/%m/%d %H:%M:%S") for x in range(len(entry.index))], allow_duplicates=True)
    entry.insert(0, 'Name', [st.session_state['name']
                 for x in range(len(entry.index))], allow_duplicates=True)
    sync_sheet()
    if len(st.session_state['df'].index) > 0:
        st.session_state['df'] = pd.concat(
            [st.session_state['df'], entry], ignore_index=True)
    else:
        st.session_state['df'] = entry
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(data=st.session_state['df'])


def reset_key():
    '''
    Increments the key used for st.data_editor object. It's stateful, so create a new object (with a new key) each time data is submitted. Possible memory leak long term?
    '''
    st.session_state['key'] += 1


if 'key' not in st.session_state:
    st.session_state['key'] = 0
if 'df' not in st.session_state or 'exercises' not in st.session_state:
    sync_sheet()

exercises = sorted([''] + st.session_state['exercises']['Exercises'].to_list())


st.title('GymTrack')
st.text('Lift tracking and analytics.')
entry_tab, analytics_tab, account_tab = st.tabs(
    [':pencil: Record', ':chart_with_upwards_trend: Analytics', f':gear: Account {signed_in_checkmark()}'])

with account_tab:
    if signed_in():
        sign_out = account_tab.button('Sign Out')
        if sign_out:
            del st.session_state['name']
            st.rerun()
    else:
        username = account_tab.text_input('Username', max_chars=10)
        sign_in = account_tab.button('Sign In')
        if sign_in:
            st.session_state['name'] = username.lower()
            st.rerun()


with entry_tab:
    if not signed_in():
        st.text('Sign In ↗️')
    else:
        emptydf = pd.DataFrame().reindex(
            columns=st.session_state['df'].columns)[['Exercise', 'Weight', 'Sets', 'Reps', 'Last-set', 'Effort']].astype({'Exercise': 'string'})
        column_config = {
            'Exercise': st.column_config.SelectboxColumn(
                'Exercise', options=exercises, required=True),
            'Weight': st.column_config.NumberColumn(
                'Weight', min_value=0, max_value=500, step=0.5, required=True),
            'Sets': st.column_config.NumberColumn(
                'Sets', min_value=1, max_value=20, step=1, required=True),
            'Reps': st.column_config.NumberColumn(
                'Reps', min_value=1, max_value=40, step=1, required=True),
            'Last-set': st.column_config.NumberColumn(
                'Last-set', min_value=1, max_value=40, step=1, required=True),
            'Effort': st.column_config.NumberColumn(
                'Effort', min_value=0, max_value=10, required=True)
        }

        entry_tab.text('Current Session')
        entry = entry_tab.data_editor(
            emptydf, hide_index=True, num_rows='dynamic', column_config=column_config, key=f'entry{st.session_state['key']}')
        submit_button = entry_tab.button('Submit')
        if submit_button and len(entry.index) > 0:
            push_data(entry)
            reset_key()
            st.rerun()

        # Exercises

        exercise_history = entry_tab.selectbox(
            'Recent Exercises', options=exercises, index=None, placeholder='Choose an exercise')
        exercise_history_df = st.session_state['df'].loc[(st.session_state['df']['Name'] == st.session_state['name']) & (
            st.session_state['df']['Exercise'] == exercise_history)].sort_values(by=['Timestamp'], ascending=False)
        exercise_history_df['Timestamp'] = exercise_history_df['Timestamp'].apply(
            lambda x: x.split(' ')[0]
        )
        exercise_history_df = exercise_history_df[[
            'Timestamp', 'Weight', 'Sets', 'Reps', 'Last-set', 'Effort']]
        exercise_history_df = exercise_history_df.rename(
            columns={'Timestamp': 'Date'})
        if len(exercise_history_df.index) > 0:
            st.dataframe(exercise_history_df.head(6), hide_index=True)

        # recent_exercises = st.session_state['df'][st.session_state['df']
        #                                           ['Name'] == st.session_state['name']].sort_values(by=['Timestamp'], ascending=False).groupby('Exercise').first()
        # # 'Exercise' column auto included as the index.
        # recent_exercises = recent_exercises[[
        #     'Weight', 'Sets', 'Reps', 'Last-set', 'Effort']]
        # if len(recent_exercises.index) > 0:
        #     st.text('Recent Exercises')
        #     st.dataframe(recent_exercises)

        # Sessions
        # Separate only the Users' data, sort in order of most recent.
        recent_sessions = st.session_state['df'][st.session_state['df']
                                                 ['Name'] == st.session_state['name']].sort_values(by=['Timestamp'], ascending=False)
        # Convert timestamp column from "date time" to "date"
        recent_sessions['Timestamp'] = recent_sessions['Timestamp'].apply(
            lambda x: x.split(' ')[0])
        # rename timestamp column
        recent_sessions = recent_sessions.rename(columns={'Timestamp': 'Date'})
        # Convert Exercise column to show set of exercises on each date.
        recent_sessions = recent_sessions.groupby('Date', sort=False)[
            'Exercise'].apply(set)
        if len(recent_sessions.index) > 0:
            st.text('Recent Sessions')
            st.dataframe(recent_sessions.head(6))


with analytics_tab:
    if not signed_in():
        st.text('Sign In ↗️')
    else:
        st.write('TODO')

        # # Raw DataFrame
        # data = st.session_state['df'][st.session_state['df']['Name'] ==
        #                               st.session_state['name']].sort_values(by=['Timestamp'], ascending=False)
        # time_removed = data.copy()
        # time_removed['Timestamp'] = time_removed['Timestamp'].apply(
        #     lambda x: x.split(' ')[0])
        # num_workouts = len(time_removed.groupby('Timestamp').count().index)
        # general_df = pd.DataFrame({
        #     'Total Workouts': [f'{num_workouts}']})
        # options = ['Data', 'General', 'Exercise Specific']
        # radio = analytics_tab.radio(
        #     label='Stats', options=options, horizontal=True, index=None)
        # if radio == 'Data':
        #     st.dataframe(data, hide_index=True)
        # elif radio == 'General':
        #     st.dataframe(general_df, hide_index=True)
        # elif radio == 'Exercise Specific':
        #     exercise = analytics_tab.selectbox(
        #         'Exercise:', options=data['Exercise'].unique(), placeholder='Choose an option')

        #     st.dataframe()
