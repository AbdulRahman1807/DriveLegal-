import 'package:flutter_test/flutter_test.dart';
import 'package:drivelegal_app/models/chat_models.dart';

void main() {
  group('Chat Models Edge Cases', () {
    test('FineResult.fromJson with null values throws or handles gracefully', () {
      final Map<String, dynamic> malformedJson = {
        'violation_name': null,
        'base_fine': null,
        'total_fine': null,
        'jurisdiction_name': null,
      };

      final result = FineResult.fromJson(malformedJson);
      expect(result.violationName, 'Unknown Violation');
      expect(result.baseFine, 0.0);
    });

    test('ChatMessage.fromBotResponse with missing citations lists', () {
      final Map<String, dynamic> emptyJson = {
        'reply': 'Test reply',
        // 'citations' is missing
        // 'fines' is missing
      };

      final result = ChatMessage.fromBotResponse(emptyJson);
      expect(result.citations, isEmpty);
      expect(result.fines, isEmpty);
    });

    test('ChatMessage.fromBotResponse with null elements in lists crashes', () {
      final Map<String, dynamic> corruptedJson = {
        'reply': 'Test reply',
        'citations': [null], // Null element inside array
        'fines': [null],
      };

      // This should now gracefully handle it by returning empty lists or dropping the nulls
      final result = ChatMessage.fromBotResponse(corruptedJson);
      expect(result.citations, isEmpty);
      expect(result.fines, isEmpty);
    });
  });
}
