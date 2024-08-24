import streamlit as st
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# streamlit run Home.py


def sync_sheet():
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.session_state['df'] = conn.read(worksheet='Data', ttl=1)
    st.session_state['exercises'] = conn.read(worksheet='Exercises', ttl=1)


def reset_this_workout():
    st.session_state['this_workout'] = pd.DataFrame().reindex(
        columns=st.session_state['df'].columns)


if 'df' not in st.session_state:
    sync_sheet()
if 'this_workout' not in st.session_state:
    reset_this_workout()


def get_previous_settings(exercise):
    '''Used to Auto-Fill exercises with the most recent values.'''
    filtered_df = st.session_state['df'][
        (st.session_state['df']['name'] == st.session_state['name']) &
        (st.session_state['df']['exercise'] == exercise)
    ]
    if len(filtered_df.index) == 0:
        return {k: 0 for k in filtered_df.columns}
    filtered_df = filtered_df.sort_values(by=['timestamp'], ascending=False)
    row_dict = filtered_df.iloc[0].to_dict()
    return row_dict


exercises = [''] + st.session_state['exercises']['exercises'].to_list()

# Row 1
with st.container():
    col_name, col_name_button, col_sync, col_add_exercise, col_add_details = st.columns(
        (9, 4, 4, 10, 5), vertical_alignment='bottom')
    username = col_name.text_input('Username', max_chars=15)
    submit = col_name_button.button('Sign In')
    if submit:
        st.session_state['name'] = username
        submit = False
    sync = col_sync.button('Sync')
    if sync:
        sync_sheet()
        st.rerun()

    add_exercise = col_add_exercise.selectbox('Exercise', options=exercises)
    add_exercise_details = col_add_details.popover('Add')
    if 'name' in st.session_state:
        with add_exercise_details.form(key='entry', clear_on_submit=True):
            most_recent = get_previous_settings(add_exercise)
            weight = st.number_input(
                'Weight (Kg)', min_value=0, value=int(most_recent['weight']))
            sets = st.number_input('# Sets', min_value=0,
                                   value=int(most_recent['sets']))
            reps = st.number_input('# Reps', min_value=0,
                                   value=int(most_recent['reps']))
            last_set = st.number_input(
                '# Reps on last set', min_value=0, value=int(most_recent['last-set']))
            effort = st.slider('Effort', min_value=0,
                               max_value=10, value=5)
            confirm = st.form_submit_button('Add')
            if confirm:
                s = pd.DataFrame([{
                    'name': st.session_state['name'],
                    'timestamp': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                    'exercise': add_exercise,
                    'weight': weight,
                    'sets': sets,
                    'reps': reps,
                    'last-set': last_set,
                    'effort': effort
                }])
                st.session_state['this_workout'] = pd.concat(
                    [st.session_state['this_workout'], s], ignore_index=True)

# Row 2
with st.container():
    if 'name' in st.session_state:
        st.text(f'Logged in --> {st.session_state['name']}')


def get_all_recent_workouts():
    filtered_df = st.session_state['df'][st.session_state['df']
                                         ['name'] == st.session_state['name']]
    filtered_df = filtered_df.sort_values(
        by=['timestamp'], ascending=False).reset_index(drop=True)
    return filtered_df[['exercise', 'timestamp', 'weight', 'sets', 'reps', 'last-set', 'effort']]


def get_particular_recent_workout(exercise):
    filtered_df = st.session_state['df'][
        (st.session_state['df']['name'] == st.session_state['name']) &
        (st.session_state['df']['exercise'] == exercise)
    ]
    filtered_df = filtered_df.sort_values(
        by=['timestamp'], ascending=False).reset_index(drop=True)
    return filtered_df[['timestamp', 'weight', 'sets', 'reps', 'last-set', 'effort']]


# Row 3
if 'name' in st.session_state:
    if not add_exercise:
        st.text('Recent Workouts: All')
        st.dataframe(get_all_recent_workouts())
    else:
        filtered = get_particular_recent_workout(add_exercise)
        if len(filtered.index) > 0:
            st.text(f'Recent Workouts: {add_exercise}')
            st.dataframe(get_particular_recent_workout(add_exercise))
        else:
            st.text(f'No {add_exercise} data')


def delete_row_by_index(index):
    st.session_state['this_workout'] = st.session_state['this_workout'].drop(
        index)
    st.session_state['this_workout'] = st.session_state['this_workout'].reset_index(
        drop=True)


def push_to_sheet():
    sync_sheet()
    st.session_state['df'] = pd.concat(
        [st.session_state['df'], st.session_state['this_workout']], ignore_index=True)
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(data=st.session_state['df'])


# Row 4
with st.container():
    session_data_col, edit_session = st.columns(
        (10, 6), vertical_alignment='top')
    if len(st.session_state['this_workout'].index) > 0:
        session_data_col.header('This Session')
        edit_session.header('Modify')
        session_data_col.dataframe(
            st.session_state['this_workout'][['exercise', 'weight', 'sets', 'reps', 'last-set', 'effort']])
        edit_input, edit_buttons = edit_session.columns(
            (10, 7), vertical_alignment='bottom')
        delete_index = edit_input.number_input('Row Index',
                                               min_value=0, max_value=max([0, len(st.session_state['this_workout'])-1]))
        del_button = edit_buttons.button('Delete')
        if del_button:
            delete_row_by_index(delete_index)
            st.rerun()

        push = st.button('Push')
        if push and len(st.session_state['this_workout'].index) > 0:
            push_to_sheet()
            reset_this_workout()
            st.rerun()
