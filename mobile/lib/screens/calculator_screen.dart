import 'package:flutter/material.dart';
import '../services/api_service.dart';

class CalculatorScreen extends StatefulWidget {
  const CalculatorScreen({super.key});

  @override
  State<CalculatorScreen> createState() => _CalculatorScreenState();
}

class _CalculatorScreenState extends State<CalculatorScreen> {
  final ApiService _apiService = ApiService();
  
  List<dynamic> _violations = [];
  List<dynamic> _jurisdictions = [];
  
  String? _selectedViolation;
  String? _selectedJurisdiction;
  String _vehicleCategory = 'ALL';
  bool _isRepeat = false;
  
  bool _isLoading = true;
  String _error = '';
  List<dynamic>? _results;

  @override
  void initState() {
    super.initState();
    _loadMetadata();
  }

  Future<void> _loadMetadata() async {
    try {
      final data = await _apiService.getCalculatorMetadata();
      setState(() {
        _violations = data['violations'] ?? [];
        _jurisdictions = data['jurisdictions'] ?? [];
        if (_violations.isNotEmpty) _selectedViolation = _violations[0]['id'];
        if (_jurisdictions.isNotEmpty) _selectedJurisdiction = _jurisdictions[0]['id'];
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _calculate() async {
    if (_selectedViolation == null || _selectedJurisdiction == null) return;
    
    setState(() {
      _isLoading = true;
      _error = '';
      _results = null;
    });

    try {
      final results = await _apiService.calculateFine(
        _selectedViolation!,
        _selectedJurisdiction!,
        _vehicleCategory,
        _isRepeat,
      );
      setState(() {
        _results = results;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading && _violations.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Fine Calculator'),
        backgroundColor: Colors.black45,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_error.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                color: Colors.red.withOpacity(0.1),
                child: Text(_error, style: const TextStyle(color: Colors.redAccent)),
              ),
            
            const Text('Violation', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedViolation,
              isExpanded: true,
              items: _violations.map<DropdownMenuItem<String>>((v) {
                return DropdownMenuItem<String>(
                  value: v['id'],
                  child: Text(v['name'], overflow: TextOverflow.ellipsis),
                );
              }).toList(),
              onChanged: (val) => setState(() => _selectedViolation = val),
              decoration: const InputDecoration(border: OutlineInputBorder()),
            ),
            
            const SizedBox(height: 16),
            const Text('Jurisdiction', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedJurisdiction,
              isExpanded: true,
              items: _jurisdictions.map<DropdownMenuItem<String>>((j) {
                return DropdownMenuItem<String>(
                  value: j['id'],
                  child: Text('${j['name']} (${j['type']})'),
                );
              }).toList(),
              onChanged: (val) => setState(() => _selectedJurisdiction = val),
              decoration: const InputDecoration(border: OutlineInputBorder()),
            ),
            
            const SizedBox(height: 16),
            const Text('Vehicle Category', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _vehicleCategory,
              items: const [
                DropdownMenuItem(value: 'ALL', child: Text('All Vehicles')),
                DropdownMenuItem(value: '2W', child: Text('Two Wheeler (2W)')),
                DropdownMenuItem(value: 'LMV', child: Text('Light Motor Vehicle')),
                DropdownMenuItem(value: 'HMV', child: Text('Heavy Motor Vehicle')),
              ],
              onChanged: (val) => setState(() => _vehicleCategory = val!),
              decoration: const InputDecoration(border: OutlineInputBorder()),
            ),
            
            const SizedBox(height: 16),
            CheckboxListTile(
              title: const Text('Repeat Offence'),
              value: _isRepeat,
              onChanged: (val) => setState(() => _isRepeat = val ?? false),
              controlAffinity: ListTileControlAffinity.leading,
              contentPadding: EdgeInsets.zero,
            ),
            
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isLoading ? null : _calculate,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                backgroundColor: Colors.tealAccent.withOpacity(0.1),
                foregroundColor: Colors.tealAccent,
              ),
              child: _isLoading 
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Calculate Fine', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ),
            
            if (_results != null) ...[
              const SizedBox(height: 32),
              const Text('Results', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const Divider(),
              if (_results!.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(16.0),
                  child: Text('No specific fines found for this combination.', style: TextStyle(color: Colors.grey)),
                )
              else
                ..._results!.map((r) => Card(
                  margin: const EdgeInsets.only(top: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(child: Text(r['violation_name'], style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.tealAccent))),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(color: Colors.white12, borderRadius: BorderRadius.circular(12)),
                              child: Text(r['jurisdiction_name'], style: const TextStyle(fontSize: 12)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('Base Fine:', style: TextStyle(color: Colors.grey)),
                            Text('₹${r['base_fine']}', style: const TextStyle(fontFamily: 'monospace')),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('Surcharges:', style: TextStyle(color: Colors.grey)),
                            Text('₹${r['surcharges']}', style: const TextStyle(fontFamily: 'monospace')),
                          ],
                        ),
                        const Divider(height: 24),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('Total Fine:', style: TextStyle(fontWeight: FontWeight.bold)),
                            Text('₹${r['total_fine']}', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.redAccent, fontFamily: 'monospace')),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Text('Legal Section: ${r['legal_section_id']}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                        if (r['imprisonment_months'] != null)
                          Text('Imprisonment: Up to ${r['imprisonment_months']} months', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                        if (r['license_suspension_months'] != null)
                          Text('License Suspension: ${r['license_suspension_months']} months', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                      ],
                    ),
                  ),
                )).toList(),
            ]
          ],
        ),
      ),
    );
  }
}
