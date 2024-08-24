import streamlit as st
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Create a connection object.
if 'df' not in st.session_state:
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.session_state['df'] = conn.read()

if 'name' not in st.session_state:
    st.session_state['name'] = ''

# Temporary alternative to signin


def update_name(name):
    st.session_state['name'] = name


def full_reset():
    for key in st.session_state:
        del st.session_state[key]
    st.rerun()


name = st.text_input('Username', max_chars=20,
                     placeholder=st.session_state['name'])
updatename = st.button('Sign in')
if updatename:
    update_name(name)

r = st.button('Full Reset')
if r:
    full_reset()

st.header(st.session_state['name'])

# in future this will be populated from a workout db, with exercises the user has done in the past pinned to top of list.
exercises = ['',
             'Bench Press',
             'Squat',
             'Dips',
             'Bent-over Row',
             'Pull-up']

if 'this_workout' not in st.session_state:
    st.session_state['this_workout'] = pd.DataFrame().reindex(
        columns=st.session_state['df'].columns)


with st.form(key='entry', clear_on_submit=True):
    exercise = st.selectbox('Exercise', options=exercises)
    weight = st.number_input('Weight (Kg)', min_value=0)
    sets = st.number_input('# Sets', min_value=0)
    reps = st.number_input('# Reps', min_value=0)
    last = st.number_input('# Reps on last set', min_value=0)
    effort = st.slider('Effort', min_value=0, max_value=10)
    confirm = st.form_submit_button('Add')

if confirm and st.session_state['name']:
    s = pd.DataFrame([{
        'name': st.session_state['name'],
        'timestamp': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        'exercise': exercise,
        'weight': weight,
        'sets': sets,
        'reps': reps,
        'last-set': last,
        'effort': effort
    }])
    st.session_state['this_workout'] = pd.concat(
        [st.session_state['this_workout'], s], ignore_index=True)


#     st.session_state['this_workout'].append({
#         'name': st.session_state['name'],
#         'timestamp': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
#         'exercise': exercise,
#         'weight': weight,
#         'sets': sets,
#         'reps': reps,
#         'last-set': last,
#         'effort': effort
#     })
# tw = pd.DataFrame(st.session_state['this_workout'])
# tw
st.header('This Session')
st.dataframe(st.session_state['this_workout'])


def delete_row_by_index(index):
    st.session_state['this_workout'] = st.session_state['this_workout'].drop(
        index)
    st.session_state['this_workout'] = st.session_state['this_workout'].reset_index(
        drop=True)


delete_index = st.number_input('Del row by index',
                               min_value=0, max_value=max([0, len(st.session_state['this_workout'])-1]))
del_button = st.button('Remove')
if del_button:
    delete_row_by_index(delete_index)
    st.rerun()


def push_to_sheet():
    st.session_state['df'] = pd.concat(
        [st.session_state['df'], st.session_state['this_workout']], ignore_index=True)
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(data=st.session_state['df'])


push = st.button('Push')
if push and st.session_state['this_workout'].size > 0:
    push_to_sheet()
    del st.session_state['this_workout']
    st.rerun()


st.header('Your Data')
st.dataframe(st.session_state['df'][st.session_state['df']
             ['name'] == st.session_state['name']].reset_index(drop=True))
