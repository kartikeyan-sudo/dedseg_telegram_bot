import sys
sys.path.insert(0, r'c:\Users\karti\OneDrive\Desktop\quizBot')
sys.path.insert(0, r'c:\Users\karti\OneDrive\Desktop\quizBot\DedSegBot')
import DedSegBot.main as main

outputs = []

def fake_send_message(chat_id, text, reply_markup=None):
    outputs.append(('send', chat_id, text, reply_markup))

def fake_answer(callback_query_id, text=None, show_alert=False):
    outputs.append(('answer', callback_query_id, text, show_alert))

def fake_broadcast_message(text, target_id=None):
    outputs.append(('broadcast', text, target_id))

main.send_message = fake_send_message
main.answer_callback_query = fake_answer
main.broadcast_message = fake_broadcast_message

# Test 1: Admin callback for "Broadcast All"
print("=== Test 1: Admin clicks 'Broadcast All' button ===")
callback_update = {
    'update_id': 100,
    'callback_query': {
        'id': 'cb1',
        'from': {'id': main.ADMIN_ID, 'is_bot': False, 'first_name': 'Admin'},
        'message': {'chat': {'id': main.ADMIN_ID}},
        'data': 'broadcast_all'
    }
}
main.handle_update(callback_update)

for entry in outputs:
    print(entry)

outputs.clear()

# Test 2: Admin sends a message in broadcast_all mode
print("\n=== Test 2: Admin sends broadcast message ===")
message_update = {
    'update_id': 101,
    'message': {
        'message_id': 1,
        'from': {'id': main.ADMIN_ID, 'is_bot': False, 'first_name': 'Admin'},
        'chat': {'id': main.ADMIN_ID, 'type': 'private'},
        'date': 0,
        'text': 'This is a dummy broadcast message to all groups.'
    }
}
main.handle_update(message_update)

for entry in outputs:
    print(entry)

outputs.clear()

# Test 3: Non-admin tries to click a button
print("\n=== Test 3: Non-admin tries to click 'Test Bot' button ===")
non_admin_callback = {
    'update_id': 102,
    'callback_query': {
        'id': 'cb2',
        'from': {'id': 999, 'is_bot': False, 'first_name': 'User'},
        'message': {'chat': {'id': 999}},
        'data': 'test'
    }
}
main.handle_update(non_admin_callback)

for entry in outputs:
    print(entry)

print("\n✅ All tests completed.")
