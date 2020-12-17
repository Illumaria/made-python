from lms import VideoItem, CompositeLearningItem, Quiz, ProgrammingAssignment


def test_composite_works():
    video_item_1 = VideoItem(name="Composite Design Pattern", length=20)
    video_item_2 = VideoItem(name="Composite Design Pattern v.2", length=10)
    lesson_composite = CompositeLearningItem(name="Lesson on composite")
    lesson_composite.add(video_item_1)
    lesson_composite.add(video_item_2)
    expected_composite_study_time = 20 * 1.5 + 10 * 1.5
    assert expected_composite_study_time == lesson_composite.estimate_study_time()

    video_item_3 = VideoItem(name="Adapter Design Pattern", length=20)
    quiz = Quiz(name="Adapter Design Pattern Quiz", questions=["a", "b", "c"])
    lesson_adapter = CompositeLearningItem(name="Lesson on adapter", learning_items=[video_item_3, quiz])
    expected_adapter_study_time = 20 * 1.5 + 3 * 5
    assert expected_adapter_study_time == lesson_adapter.estimate_study_time()

    module_design_patterns = CompositeLearningItem(name="Design Patterns", learning_items=[lesson_composite, lesson_adapter])
    module_design_patterns.add(
        ProgrammingAssignment(name="Factory Method Programming Assignment", language="python")
    )
    assert expected_composite_study_time + expected_adapter_study_time + 120 == module_design_patterns.estimate_study_time()
