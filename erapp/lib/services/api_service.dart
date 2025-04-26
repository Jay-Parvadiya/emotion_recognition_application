import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:typed_data';

class ApiService {
  // Use 0.0.0.0 for web
  static const String webUrl = 'http://localhost:5000';
  // Use 10.0.2.2 for Android emulator, localhost for iOS simulator
  static const String mobileUrl = 'http://10.0.2.2:5000';

  String get baseUrl => kIsWeb ? webUrl : mobileUrl;

  Future<Map<String, dynamic>> detectEmotion(String imagePath, [Uint8List? webImage]) async {
    try {
      print('Starting emotion detection request');
      print('Platform: ${kIsWeb ? 'Web' : 'Mobile'}');
      print('Using backend URL: $baseUrl');
      print('Image path: $imagePath');
      
      final url = Uri.parse('$baseUrl/detect_emotion');
      var request = http.MultipartRequest('POST', url);

      if (kIsWeb && webImage != null) {
        print('Processing web image of size: ${webImage.length} bytes');
        request.files.add(
          http.MultipartFile.fromBytes(
            'image',
            webImage,
            filename: 'image.jpg',
          ),
        );
      } else {
        print('Processing mobile image from path');
        request.files.add(
          await http.MultipartFile.fromPath('image', imagePath),
        );
      }

      print('Sending request...');
      final streamedResponse = await request.send().timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          throw Exception('Request timed out after 30 seconds');
        },
      );
      
      print('Received response, processing...');
      final response = await http.Response.fromStream(streamedResponse);

      print('Response status code: ${response.statusCode}');
      print('Response headers: ${response.headers}');
      print('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final Map<String, dynamic> result = json.decode(response.body);
        print('Successfully parsed result: $result');
        return result;
      } else {
        print('Error response: ${response.body}');
        throw Exception('Failed to detect emotion: Status ${response.statusCode}, Body: ${response.body}');
      }
    } catch (e, stackTrace) {
      print('Error in detectEmotion: $e');
      print('Stack trace: $stackTrace');
      throw Exception('Error: $e');
    }
  }
} 