class Citation {
  final String actName;
  final String section;
  final String? clause;
  final double? relevanceScore;

  Citation({
    required this.actName,
    required this.section,
    this.clause,
    this.relevanceScore,
  });

  factory Citation.fromJson(Map<String, dynamic> json) {
    return Citation(
      actName: json['act_name'] ?? 'Unknown Act',
      section: json['section'] ?? '',
      clause: json['clause'],
      relevanceScore: (json['relevance_score'] as num?)?.toDouble(),
    );
  }
}

class FineResult {
  final String violationName;
  final double baseFine;
  final double totalFine;
  final String jurisdictionName;
  final String? note;
  final int? imprisonmentMonths;
  final int? licenseSuspensionMonths;

  FineResult({
    required this.violationName,
    required this.baseFine,
    required this.totalFine,
    required this.jurisdictionName,
    this.note,
    this.imprisonmentMonths,
    this.licenseSuspensionMonths,
  });

  factory FineResult.fromJson(Map<String, dynamic> json) {
    return FineResult(
      violationName: json['violation_name'] ?? 'Unknown Violation',
      baseFine: (json['base_fine'] as num?)?.toDouble() ?? 0.0,
      totalFine: (json['total_fine'] as num?)?.toDouble() ?? 0.0,
      jurisdictionName: json['jurisdiction_name'] ?? 'Unknown',
      note: json['note'],
      imprisonmentMonths: json['imprisonment_months'] as int?,
      licenseSuspensionMonths: json['license_suspension_months'] as int?,
    );
  }
}

class ChatMessage {
  final String text;
  final bool isUser;
  final List<Citation> citations;
  final List<FineResult> fines;
  final bool isError;

  ChatMessage({
    required this.text,
    required this.isUser,
    this.citations = const [],
    this.fines = const [],
    this.isError = false,
  });

  factory ChatMessage.fromBotResponse(Map<String, dynamic> json) {
    var citationsList = json['citations'] as List? ?? [];
    var finesList = json['fines'] as List? ?? [];

    return ChatMessage(
      text: json['reply'] ?? '',
      isUser: false,
      citations: citationsList.whereType<Map<String, dynamic>>().map((c) => Citation.fromJson(c)).toList(),
      fines: finesList.whereType<Map<String, dynamic>>().map((f) => FineResult.fromJson(f)).toList(),
    );
  }
}
