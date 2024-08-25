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
    st.session_state['exercises'] = conn.read(worksheet='Exercises', ttl=1)


def reset_this_workout():
    '''
    Empties the "this_workout" dataframe.
    '''
    st.session_state['this_workout'] = pd.DataFrame().reindex(
        columns=st.session_state['df'].columns)


def get_previous_settings(exercise):
    '''
    Used to Auto-Fill exercise details with their most recent numbers.
    Returns: dictionary. If no previous settings found, dict values will all be 0.
    '''
    filtered_df = st.session_state['df'][
        (st.session_state['df']['Name'] == st.session_state['name']) &
        (st.session_state['df']['Exercise'] == exercise)
    ]
    if len(filtered_df.index) == 0:
        return {k: 0 for k in filtered_df.columns}
    filtered_df = filtered_df.sort_values(by=['Timestamp'], ascending=False)
    row_dict = filtered_df.iloc[0].to_dict()
    return row_dict


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


def delete_row_by_index(index):
    '''
    Deletes given row of the "this_workout" Dataframe.
    '''
    st.session_state['this_workout'] = st.session_state['this_workout'].drop(
        index)
    st.session_state['this_workout'] = st.session_state['this_workout'].reset_index(
        drop=True)


def push_to_sheet():
    '''
    Gets most updated version of sheet, appends "this_workout" and reuploads.
    '''
    sync_sheet()
    st.session_state['df'] = pd.concat(
        [st.session_state['df'], st.session_state['this_workout']], ignore_index=True)
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(data=st.session_state['df'])


if 'df' not in st.session_state or 'exercises' not in st.session_state:
    sync_sheet()
if 'this_workout' not in st.session_state:
    reset_this_workout()
exercises = [''] + st.session_state['exercises']['Exercises'].to_list()


st.title('GymTrack')

st.text('Lift tracking and analytics.')
entry_tab, analytics_tab, account_tab = st.tabs(
    [':pencil: Record', ':chart_with_upwards_trend: Stats', f':gear: Account {signed_in_checkmark()}'])

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
            st.session_state['name'] = username
            st.rerun()
with entry_tab:
    if not signed_in():
        entry_tab.text('First, sign in')
    else:
        with entry_tab.container():
            add_exercise = entry_tab.selectbox(
                'Exercise', key='add_exercise_widget', options=exercises)
            if add_exercise:
                add_exercise_details = entry_tab.popover('Add')
                with add_exercise_details.form(key='entry', clear_on_submit=True):
                    most_recent = get_previous_settings(add_exercise)
                    weight = st.number_input(
                        'Weight (Kg)', min_value=0, value=int(most_recent['Weight']))
                    sets = st.number_input('# Sets', min_value=0,
                                           value=int(most_recent['Sets']))
                    reps = st.number_input('# Reps', min_value=0,
                                           value=int(most_recent['Reps']))
                    last_set = st.number_input(
                        '# Reps on last set', min_value=0, value=int(most_recent['Last-set']))
                    effort = st.slider('Effort', min_value=0,
                                       max_value=10, value=5)
                    confirm = st.form_submit_button(
                        'Add')
                    if confirm:
                        s = pd.DataFrame([{
                            'Name': st.session_state['name'],
                            'Timestamp': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                            'Exercise': add_exercise,
                            'Weight': weight,
                            'Sets': sets,
                            'Reps': reps,
                            'Last-set': last_set,
                            'Effort': effort
                        }])
                        st.session_state['this_workout'] = pd.concat(
                            [st.session_state['this_workout'], s], ignore_index=True)
        with entry_tab.container():
            if len(st.session_state['this_workout'].index) > 0:
                entry_tab.text('Current Session')
                entry_tab.dataframe(st.session_state['this_workout'][[
                                    'Exercise', 'Weight', 'Sets', 'Reps', 'Last-set', 'Effort']])
                c1, c2 = entry_tab.columns([0.8, 0.2])

                delete_index = c1.number_input('Select row index to delete',
                                               min_value=0, max_value=max([0, len(st.session_state['this_workout'].index)-1]), )
                del_button = c2.button('D')
                if del_button:
                    delete_row_by_index(delete_index)
                    st.rerun()
                push = entry_tab.button('Submit')
                if push:
                    try:
                        push_to_sheet()
                    except:
                        st.text('Something went wrong')
                    reset_this_workout()
                    st.rerun()


# # Empty entry for default value.
# exercises = [''] + st.session_state['exercises']['exercises'].to_list()

# # Row 1
# with st.container():
#     col_name, col_name_button, col_sync, col_add_exercise, col_add_details = st.columns(
#         (9, 4, 4, 10, 5), vertical_alignment='bottom')
#     username = col_name.text_input('Username', max_chars=15)
#     submit = col_name_button.button('Sign In')
#     if submit:
#         st.session_state['name'] = username
#         submit = False
#     sync = col_sync.button('Sync')
#     if sync:
#         sync_sheet()
#         st.rerun()

#     add_exercise = col_add_exercise.selectbox('Exercise', options=exercises)
#     add_exercise_details = col_add_details.popover('Add')
#     if 'name' in st.session_state:
#         with add_exercise_details.form(key='entry', clear_on_submit=True):
#             most_recent = get_previous_settings(add_exercise)
#             weight = st.number_input(
#                 'Weight (Kg)', min_value=0, value=int(most_recent['weight']))
#             sets = st.number_input('# Sets', min_value=0,
#                                    value=int(most_recent['sets']))
#             reps = st.number_input('# Reps', min_value=0,
#                                    value=int(most_recent['reps']))
#             last_set = st.number_input(
#                 '# Reps on last set', min_value=0, value=int(most_recent['last-set']))
#             effort = st.slider('Effort', min_value=0,
#                                max_value=10, value=5)
#             confirm = st.form_submit_button('Add')
#             if confirm:
#                 s = pd.DataFrame([{
#                     'name': st.session_state['name'],
#                     'timestamp': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
#                     'exercise': add_exercise,
#                     'weight': weight,
#                     'sets': sets,
#                     'reps': reps,
#                     'last-set': last_set,
#                     'effort': effort
#                 }])
#                 st.session_state['this_workout'] = pd.concat(
#                     [st.session_state['this_workout'], s], ignore_index=True)

# # Row 2
# with st.container():
#     if 'name' in st.session_state:
#         st.text(f'Logged in --> {st.session_state['name']}')


# def get_all_recent_workouts():
#     '''
#     Filters by user, sorts by timestamp.
#     Returns: pd.Dataframe
#     '''
#     filtered_df = st.session_state['df'][st.session_state['df']
#                                          ['name'] == st.session_state['name']]
#     filtered_df = filtered_df.sort_values(
#         by=['timestamp'], ascending=False).reset_index(drop=True)
#     return filtered_df[['exercise', 'timestamp', 'weight', 'sets', 'reps', 'last-set', 'effort']]


# def get_particular_recent_workout(exercise):
#     '''
#     Filters by name and exercise, sorts by timestamp.
#     Returns: pd.Dataframe.
#     '''
#     filtered_df = st.session_state['df'][
#         (st.session_state['df']['name'] == st.session_state['name']) &
#         (st.session_state['df']['exercise'] == exercise)
#     ]
#     filtered_df = filtered_df.sort_values(
#         by=['timestamp'], ascending=False).reset_index(drop=True)
#     return filtered_df[['timestamp', 'weight', 'sets', 'reps', 'last-set', 'effort']]


# # Row 3
# if 'name' in st.session_state:
#     if not add_exercise:
#         st.text('Recent Workouts: All')
#         st.dataframe(get_all_recent_workouts())
#     else:
#         filtered = get_particular_recent_workout(add_exercise)
#         if len(filtered.index) > 0:
#             st.text(f'Recent Workouts: {add_exercise}')
#             st.dataframe(get_particular_recent_workout(add_exercise))
#         else:
#             st.text(f'No {add_exercise} data')


# def delete_row_by_index(index):
#     '''
#     Deletes given row of the "this_workout" Dataframe.
#     '''
#     st.session_state['this_workout'] = st.session_state['this_workout'].drop(
#         index)
#     st.session_state['this_workout'] = st.session_state['this_workout'].reset_index(
#         drop=True)


# def push_to_sheet():
#     '''
#     Gets most updated version of sheet, appends "this_workout" and reuploads.
#     '''
#     sync_sheet()
#     st.session_state['df'] = pd.concat(
#         [st.session_state['df'], st.session_state['this_workout']], ignore_index=True)
#     conn = st.connection("gsheets", type=GSheetsConnection)
#     conn.update(data=st.session_state['df'])


# # Row 4
# with st.container():
#     session_data_col, edit_session = st.columns(
#         (10, 6), vertical_alignment='top')
#     if len(st.session_state['this_workout'].index) > 0:
#         session_data_col.header('This Session')
#         edit_session.header('Modify')
#         session_data_col.dataframe(
#             st.session_state['this_workout'][['exercise', 'weight', 'sets', 'reps', 'last-set', 'effort']])
#         edit_input, edit_buttons = edit_session.columns(
#             (10, 7), vertical_alignment='bottom')
#         delete_index = edit_input.number_input('Row Index',
#                                                min_value=0, max_value=max([0, len(st.session_state['this_workout'])-1]))
#         del_button = edit_buttons.button('Delete')
#         if del_button:
#             delete_row_by_index(delete_index)
#             st.rerun()

#         push = st.button('Push')
#         if push and len(st.session_state['this_workout'].index) > 0:
#             push_to_sheet()
#             reset_this_workout()
#             st.rerun()
