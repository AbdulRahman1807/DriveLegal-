import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class CitationChip extends StatelessWidget {
  const CitationChip({super.key, required this.citation, this.api});

  final Map<String, dynamic> citation;
  final ApiService? api;

  @override
  Widget build(BuildContext context) {
    final act = citation['act_name']?.toString() ?? 'Act';
    final sec = citation['section']?.toString() ?? '';
    return InkWell(
      onTap: () => _openModal(context),
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10.4, vertical: 5.6),
        decoration: BoxDecoration(
          color: DriveLegalColors.inputBg,
          borderRadius: BorderRadius.circular(999),
          border: Border.all(color: DriveLegalColors.borderPrimary),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.menu_book_outlined, size: 12, color: DriveLegalColors.chipText),
            const SizedBox(width: 5.6),
            Flexible(
              child: Text(
                '$act · Sec. $sec',
                style: DriveLegalTheme.text(12, weight: FontWeight.w600, color: DriveLegalColors.chipText),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openModal(BuildContext context) async {
    final service = api ?? ApiService();
    showDialog(
      context: context,
      barrierColor: const Color(0xA6000000),
      builder: (_) => const Center(child: CircularProgressIndicator(color: DriveLegalColors.primary)),
    );
    try {
      final id = citation['id']?.toString();
      if (id == null) throw Exception('Missing citation id');
      final detail = await service.getLegalSection(id);
      if (!context.mounted) return;
      Navigator.pop(context);
      showDialog(
        context: context,
        barrierColor: const Color(0xA6000000),
        builder: (ctx) => Dialog(
          backgroundColor: DriveLegalColors.card,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: DriveLegalColors.borderStrong),
          ),
          child: ConstrainedBox(
            constraints: BoxConstraints(maxWidth: 520, maxHeight: MediaQuery.sizeOf(ctx).height * 0.8),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('FROM THIS ANSWER', style: DriveLegalTheme.text(10.9, weight: FontWeight.w700, color: DriveLegalColors.accent).copyWith(letterSpacing: 1.2)),
                  const SizedBox(height: 6),
                  Text('Section ${detail['section_number']}', style: DriveLegalTheme.text(20, weight: FontWeight.w700)),
                  Text(detail['act_name']?.toString() ?? '', style: DriveLegalTheme.text(14, color: DriveLegalColors.muted)),
                  const SizedBox(height: 16),
                  Flexible(
                    child: SingleChildScrollView(
                      child: Text(detail['full_text']?.toString() ?? '', style: DriveLegalTheme.text(14, height: 1.55)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close')),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    } catch (e) {
      if (context.mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }
}
