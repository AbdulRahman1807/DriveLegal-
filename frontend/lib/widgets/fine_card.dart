import 'package:flutter/material.dart';
import '../models/chat_models.dart';
import '../theme/app_theme.dart';

class FineCard extends StatelessWidget {
  final FineResult fine;

  const FineCard({Key? key, required this.fine}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 48.0, bottom: 8.0, right: 16.0),
      child: Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.currency_rupee, color: Colors.redAccent, size: 20),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      fine.violationName,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Base Fine: ₹${fine.baseFine.toStringAsFixed(0)}',
                      style: const TextStyle(color: AppColors.textSecondary, fontSize: 13),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Total Fine: ₹${fine.totalFine.toStringAsFixed(0)}',
                      style: const TextStyle(color: Colors.redAccent, fontSize: 13, fontWeight: FontWeight.bold),
                    ),
                    if (fine.note != null && fine.note!.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        fine.note!,
                        style: const TextStyle(color: AppColors.textSecondary, fontSize: 12, fontStyle: FontStyle.italic),
                      ),
                    ],
                    if (fine.imprisonmentMonths != null && fine.imprisonmentMonths! > 0) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(Icons.warning, color: Colors.orange, size: 14),
                          const SizedBox(width: 4),
                          Text(
                            'Up to ${fine.imprisonmentMonths} months imprisonment',
                            style: const TextStyle(color: Colors.orange, fontSize: 12, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ],
                    if (fine.licenseSuspensionMonths != null && fine.licenseSuspensionMonths! > 0) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(Icons.warning, color: Colors.orange, size: 14),
                          const SizedBox(width: 4),
                          Text(
                            'Up to ${fine.licenseSuspensionMonths} months license suspension',
                            style: const TextStyle(color: Colors.orange, fontSize: 12, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ]
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
