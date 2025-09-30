#!/usr/bin/env python3
"""
Test script to verify the Callosum Python integration works correctly
"""

from callosum_dsl import Callosum, PersonalityAI, PERSONALITY_TEMPLATES, CallosumError
import json

def test_basic_functionality():
    """Test basic compilation functionality"""
    print("🧪 Testing Basic Functionality...")
    
    callosum = Callosum()
    
    simple_dsl = '''personality: "Test Assistant"

traits:
  helpfulness: 0.9
  patience: 0.8
  
knowledge:
  domain support:
    problem_solving: expert
  
behaviors:
  - when helpfulness > 0.8 → seek "solutions"'''
    
    # Test JSON compilation
    personality = callosum.to_json(simple_dsl)
    assert personality['name'] == "Test Assistant"
    assert len(personality['traits']) == 2
    print("  ✅ JSON compilation works")
    
    # Test prompt compilation
    prompt = callosum.to_prompt(simple_dsl)
    assert "Test Assistant" in prompt
    assert "helpfulness" in prompt.lower()
    print("  ✅ Prompt compilation works")
    
    # Test Lua compilation
    lua = callosum.to_lua(simple_dsl)
    assert "Test Assistant" in lua
    assert "personality.traits" in lua
    print("  ✅ Lua compilation works")
    
    print("  🎉 All basic functionality tests passed!")

def test_personality_templates():
    """Test the ready-made personality templates"""
    print("\n🎨 Testing Personality Templates...")
    
    callosum = Callosum()
    
    for name, dsl in PERSONALITY_TEMPLATES.items():
        try:
            personality = callosum.to_json(dsl)
            print(f"  ✅ {name}: '{personality['name']}' - {len(personality['traits'])} traits")
        except Exception as e:
            print(f"  ❌ {name}: Failed - {e}")
            raise
    
    print("  🎉 All templates work correctly!")

def test_error_handling():
    """Test error handling for invalid DSL"""
    print("\n🚨 Testing Error Handling...")
    
    callosum = Callosum()
    
    # Test invalid DSL syntax
    invalid_dsl = '''personality: "Broken"

traits:
  invalid_trait: 1.5  # Invalid strength > 1.0'''
    
    try:
        callosum.to_json(invalid_dsl)
        assert False, "Should have raised an error"
    except CallosumError:
        print("  ✅ Invalid DSL properly rejected")
    
    # Test empty DSL
    try:
        callosum.to_json("")
        assert False, "Should have raised an error"  
    except CallosumError:
        print("  ✅ Empty DSL properly rejected")
    
    # Test validation method
    assert callosum.validate(PERSONALITY_TEMPLATES["helpful_assistant"])
    assert not callosum.validate(invalid_dsl)
    print("  ✅ Validation method works")
    
    print("  🎉 Error handling works correctly!")

def test_all_output_formats():
    """Test all compilation targets"""
    print("\n🎯 Testing All Output Formats...")
    
    callosum = Callosum()
    dsl = PERSONALITY_TEMPLATES["helpful_assistant"]
    
    formats = ["json", "prompt", "lua", "sql", "cypher"]
    
    for fmt in formats:
        try:
            output = callosum.compile(dsl, fmt)
            assert output.strip(), f"{fmt} output should not be empty"
            print(f"  ✅ {fmt.upper()} compilation works")
        except Exception as e:
            print(f"  ❌ {fmt.upper()} compilation failed: {e}")
            raise
    
    print("  🎉 All output formats work!")

def test_performance():
    """Test compilation performance"""
    print("\n⚡ Testing Performance...")
    
    import time
    callosum = Callosum()
    dsl = PERSONALITY_TEMPLATES["helpful_assistant"]
    
    # Test compilation speed
    start_time = time.time()
    for _ in range(10):
        personality = callosum.to_json(dsl)
    
    elapsed = time.time() - start_time
    avg_time = elapsed / 10
    
    print(f"  📊 Average compilation time: {avg_time*1000:.1f}ms")
    
    if avg_time < 0.5:  # Should be under 500ms
        print("  ✅ Performance is good")
    else:
        print("  ⚠️  Performance could be better")
    
    print("  🎉 Performance test complete!")

def main():
    """Run all tests"""
    print("🚀 Callosum Python Integration Test Suite")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_personality_templates()
        test_error_handling()
        test_all_output_formats()
        test_performance()
        
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\n✨ Your Callosum Python integration is working perfectly!")
        print("\n📚 Next steps:")
        print("   • Check out README_PYTHON.md for usage examples")
        print("   • Try the PersonalityAI class with your AI API keys")
        print("   • Create your own custom personalities")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Make sure the DSL is built: cd personality/dsl && dune build")
        print("   • Check that the compiler binary exists")
        return False
    
    return True

if __name__ == "__main__":
    main()
