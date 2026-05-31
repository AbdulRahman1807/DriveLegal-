import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../models/chat_models.dart';
import '../theme/app_theme.dart';
import 'citation_card.dart';
import 'fine_card.dart';

class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({Key? key, required this.message}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 16.0),
      child: Column(
        crossAxisAlignment: message.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!message.isUser) ...[
                const CircleAvatar(
                  backgroundColor: AppColors.primary,
                  child: Icon(Icons.gavel, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 8),
              ],
              Flexible(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: message.isError 
                        ? Colors.red.shade50 
                        : (message.isUser ? AppColors.chatBubbleUser : AppColors.primary),
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(16),
                      topRight: const Radius.circular(16),
                      bottomLeft: Radius.circular(message.isUser ? 16 : 0),
                      bottomRight: Radius.circular(message.isUser ? 0 : 16),
                    ),
                  ),
                  child: message.isUser 
                      ? Text(
                          message.text,
                          style: TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 16,
                          ),
                        )
                      : Builder(
                          builder: (context) {
                            try {
                              return MarkdownBody(
                                data: message.text,
                                styleSheet: MarkdownStyleSheet(
                                  p: const TextStyle(color: Colors.white, fontSize: 15, height: 1.4),
                                  strong: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                                ),
                              );
                            } catch (_) {
                              return Text(
                                message.text,
                                style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.4),
                              );
                            }
                          }
                        ),
                ),
              ),
              if (message.isUser) const SizedBox(width: 40), // Spacing for user messages
            ],
          ),
          
          // Render Fines Below AI Message
          if (message.fines.isNotEmpty) ...[
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.only(left: 48.0),
              child: Text(
                "APPLICABLE FINES", 
                style: Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.bold, letterSpacing: 0.5),
              ),
            ),
            const SizedBox(height: 4),
            ...message.fines.map((fine) => FineCard(fine: fine)).toList(),
          ],

          // Render Citations Below AI Message
          if (message.citations.isNotEmpty) ...[
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.only(left: 48.0),
              child: Text(
                "LEGAL CITATIONS", 
                style: Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.bold, letterSpacing: 0.5),
              ),
            ),
            const SizedBox(height: 4),
            ...message.citations.map((cit) => CitationCard(citation: cit)).toList(),
          ],
        ],
      ),
    );
  }
}
