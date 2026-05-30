#!/usr/bin/env python3
"""
多媒体课件支持功能测试脚本
验证视频上传、3D模型处理、文档处理等功能
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models.multimedia import (
    MultimediaResource, MediaType, VideoStatus, DocumentFormat
)
from services.multimedia_service import MultimediaService
from services.three_d_service import ThreeDModelService
from services.document_service import DocumentProcessingService

class TestMultimediaModels(unittest.TestCase):
    """测试多媒体模型"""
    
    def test_media_type_enum(self):
        """测试媒体类型枚举"""
        self.assertEqual(MediaType.VIDEO.value, "video")
        self.assertEqual(MediaType.DOCUMENT.value, "document")
        self.assertEqual(MediaType.THREE_D_MODEL.value, "3d_model")
        
    def test_video_status_enum(self):
        """测试视频状态枚举"""
        self.assertEqual(VideoStatus.UPLOADED.value, "uploaded")
        self.assertEqual(VideoStatus.READY.value, "ready")
        self.assertEqual(VideoStatus.FAILED.value, "failed")
        
    def test_document_format_enum(self):
        """测试文档格式枚举"""
        self.assertEqual(DocumentFormat.PDF.value, "pdf")
        self.assertEqual(DocumentFormat.MARKDOWN.value, "markdown")
        self.assertEqual(DocumentFormat.PPTX.value, "pptx")

class TestMultimediaService(unittest.TestCase):
    """测试多媒体服务"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock()
        self.service = MultimediaService(self.mock_db)
        
    def test_create_multimedia_resource(self):
        """测试创建多媒体资源"""
        # 准备测试数据
        resource_data = Mock()
        resource_data.course_id = 1
        resource_data.lesson_id = None
        resource_data.title = "测试视频"
        resource_data.description = "测试描述"
        resource_data.media_type = MediaType.VIDEO
        resource_data.file_name = "test.mp4"
        resource_data.file_size = 1024000
        resource_data.mime_type = "video/mp4"
        resource_data.is_public = False
        resource_data.access_level = "course"
        resource_data.tags = ["test"]
        resource_data.metadata = {}
        
        mock_course = Mock()
        mock_course.id = 1
        mock_user = Mock()
        mock_user.id = 1
        
        # 模拟数据库查询
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_course
        
        # 执行测试
        with patch.object(self.service, '_can_manage_resource', return_value=True):
            result = self.service.create_multimedia_resource(1, resource_data, mock_user)
            
        # 验证结果
        self.assertIsInstance(result, MultimediaResource)
        self.assertEqual(result.title, "测试视频")
        self.assertEqual(result.media_type, MediaType.VIDEO)
        
    def test_get_course_multimedia(self):
        """测试获取课程多媒体资源"""
        # 准备测试数据
        mock_resources = [Mock(), Mock()]
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_resources
        
        with patch.object(self.mock_db, 'query', return_value=mock_query):
            result = self.service.get_course_multimedia(1, 1, MediaType.VIDEO)
            
        # 验证结果
        self.assertEqual(len(result), 2)
        mock_query.filter.assert_called_once()

class TestThreeDService(unittest.TestCase):
    """测试3D模型服务"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock()
        self.service = ThreeDModelService(self.mock_db)
        
    def test_supported_formats(self):
        """测试支持的3D格式"""
        formats = self.service.get_supported_formats()
        expected_formats = ['obj', 'stl', 'glb', 'gltf']
        self.assertEqual(formats, expected_formats)
        
    def test_validate_obj_file(self):
        """测试OBJ文件验证"""
        # 有效的OBJ文件内容
        valid_obj = b"v 1.0 2.0 3.0\nv 4.0 5.0 6.0\nf 1 2 3"
        self.assertTrue(self.service._validate_obj_file(valid_obj))
        
        # 无效的文件内容
        invalid_obj = b"invalid content"
        self.assertFalse(self.service._validate_obj_file(invalid_obj))
        
    def test_validate_stl_file(self):
        """测试STL文件验证"""
        # ASCII STL文件
        ascii_stl = b"solid test\nendsolid test"
        self.assertTrue(self.service._validate_stl_file(ascii_stl))
        
        # 二进制STL文件头
        binary_stl = b"\x00" * 80 + b"\x00\x00\x00\x00" + b"\x00" * 100
        self.assertTrue(self.service._validate_stl_file(binary_stl))

class TestDocumentService(unittest.TestCase):
    """测试文档处理服务"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock()
        self.service = DocumentProcessingService(self.mock_db)
        
    def test_supported_formats(self):
        """测试支持的文档格式"""
        formats = self.service.get_supported_formats()
        expected_values = ['pdf', 'markdown', 'pptx', 'docx', 'txt', 'html']
        actual_values = [f.value for f in formats]
        self.assertEqual(actual_values, expected_values)
        
    def test_detect_document_format(self):
        """测试文档格式检测"""
        # PDF文件
        pdf_data = b"%PDF-1.4\n..."
        format_pdf = self.service._detect_document_format("test.pdf", pdf_data)
        self.assertEqual(format_pdf, DocumentFormat.PDF)
        
        # Markdown文件
        md_data = b"# Test\nContent"
        format_md = self.service._detect_document_format("test.md", md_data)
        self.assertEqual(format_md, DocumentFormat.MARKDOWN)
        
        # HTML文件
        html_data = b"<!DOCTYPE html><html><body>Test</body></html>"
        format_html = self.service._detect_document_format("test.html", html_data)
        self.assertEqual(format_html, DocumentFormat.HTML)
        
    def test_validate_pdf_file(self):
        """测试PDF文件验证"""
        valid_pdf = b"%PDF-1.4"
        invalid_pdf = b"Not a PDF"
        
        self.assertTrue(self.service._validate_pdf_file(valid_pdf))
        self.assertFalse(self.service._validate_pdf_file(invalid_pdf))
        
    def test_validate_docx_file(self):
        """测试DOCX文件验证"""
        # DOCX是ZIP格式，包含特定文件
        valid_docx = b"PK\x03\x04" + b"[Content_Types].xml" + b"x" * 100
        invalid_docx = b"Not a DOCX"
        
        self.assertTrue(self.service._validate_docx_file(valid_docx))
        self.assertFalse(self.service._validate_docx_file(invalid_docx))

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_full_workflow(self):
        """测试完整的多媒体处理流程"""
        # 这里可以添加更复杂的集成测试
        # 模拟从上传到处理的完整流程
        pass

def run_tests():
    """运行所有测试"""
    print("开始运行多媒体课件支持测试...")
    print("=" * 50)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestMultimediaModels))
    suite.addTests(loader.loadTestsFromTestCase(TestMultimediaService))
    suite.addTests(loader.loadTestsFromTestCase(TestThreeDService))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentService))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
            
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)