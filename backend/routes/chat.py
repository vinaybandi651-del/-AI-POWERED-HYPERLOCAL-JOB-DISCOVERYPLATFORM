from flask import Blueprint, request, jsonify
from database.db import query_db, execute_db
from utils.security import token_required

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/conversations', methods=['GET'])
@token_required
def get_conversations():
    user_id = request.current_user['user_id']

    # Get distinct conversational partners and latest message
    query = """
        SELECT
            CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END AS other_user_id,
            u.full_name as other_user_name,
            u.avatar_url as other_user_avatar,
            u.role as other_user_role,
            j.id as job_id,
            j.title as job_title,
            m.message_text as last_message,
            m.created_at as last_message_time,
            (SELECT COUNT(*) FROM messages unread WHERE unread.sender_id = (CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END) AND unread.receiver_id = ? AND unread.is_read = 0) as unread_count
        FROM messages m
        JOIN users u ON u.id = (CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END)
        LEFT JOIN jobs j ON m.job_id = j.id
        WHERE m.id IN (
            SELECT MAX(id)
            FROM messages
            WHERE sender_id = ? OR receiver_id = ?
            GROUP BY CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END
        )
        ORDER BY m.created_at DESC
    """
    conversations = query_db(query, (user_id, user_id, user_id, user_id, user_id, user_id, user_id))
    return jsonify({'conversations': conversations})

@chat_bp.route('/messages/<int:other_user_id>', methods=['GET'])
@token_required
def get_messages(other_user_id):
    user_id = request.current_user['user_id']
    job_id = request.args.get('job_id', type=int)

    query = """
        SELECT m.*, u.full_name as sender_name, u.avatar_url as sender_avatar
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE ((m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?))
    """
    params = [user_id, other_user_id, other_user_id, user_id]

    if job_id:
        query += " AND m.job_id = ?"
        params.append(job_id)

    query += " ORDER BY m.created_at ASC"

    messages = query_db(query, params)

    # Mark unread messages as read
    execute_db("""
        UPDATE messages SET is_read = 1
        WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
    """, (other_user_id, user_id))

    other_user = query_db("SELECT id, full_name, role, avatar_url FROM users WHERE id = ?", (other_user_id,), one=True)

    return jsonify({'messages': messages, 'other_user': other_user})

@chat_bp.route('/messages', methods=['POST'])
@token_required
def send_message():
    sender_id = request.current_user['user_id']
    data = request.get_json() or {}
    receiver_id = data.get('receiver_id')
    message_text = (data.get('message_text') or data.get('message') or '').strip()
    job_id = data.get('job_id')
    application_id = data.get('application_id')

    if not receiver_id or not message_text:
        return jsonify({'error': 'receiver_id and message_text are required'}), 400

    msg_id = execute_db("""
        INSERT INTO messages (job_id, application_id, sender_id, receiver_id, message_text, is_read)
        VALUES (?, ?, ?, ?, ?, 0)
    """, (job_id, application_id, sender_id, receiver_id, message_text))

    # Send in-app notification
    sender_name = request.current_user['full_name']
    execute_db("""
        INSERT INTO notifications (user_id, title, message, type, link)
        VALUES (?, ?, ?, 'message', 'chat.html')
    """, (receiver_id, f"New message from {sender_name}", message_text[:60] + ('...' if len(message_text) > 60 else '')))

    new_msg = query_db("""
        SELECT m.*, u.full_name as sender_name, u.avatar_url as sender_avatar
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.id = ?
    """, (msg_id,), one=True)

    return jsonify({'message': new_msg}), 201
