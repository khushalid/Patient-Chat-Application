from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from chat.models import Chat, Message
from django.utils.timezone import localtime

@login_required
def chat_main(request):
    try:
        chat, created = Chat.objects.get_or_create(user=request.user)
    except:
        chat = Chat(user = request.user)
        chat.save()

    return redirect('chat_id', pk=chat.id)



def chat(request, pk):
    chat = Chat.objects.get(id=pk)
    messages = Message.objects.filter(chat=chat).order_by('id')

    # Format messages with timestamps
    formatted_messages = []
    for message in messages:
        formatted_messages.append({
            'content': message.message,
            'is_user': message.is_user,
            'timestamp': localtime(message.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        })

    return render(request, 'chat/chat.html', {
        'messages': formatted_messages,
        'chat_id': pk
    })

@login_required
def clear_chat(request, pk):
    if request.method == 'POST':
        chat = Chat.objects.get(id=pk)
        # Delete all messages in the chat
        Message.objects.filter(chat=chat).delete()
        
        # Redirect to the chat page after clearing
        return redirect('chat_id', pk=pk)



    