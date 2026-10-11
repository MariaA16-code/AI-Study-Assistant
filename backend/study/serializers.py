from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    question = serializers.CharField(max_length=2000)


class GenerateRequestSerializer(serializers.Serializer):
    document_id = serializers.IntegerField()
    question_type = serializers.ChoiceField(choices=["mcq", "short", "long", "mixed"])
    difficulty = serializers.ChoiceField(choices=["low", "medium", "high"])
    count = serializers.IntegerField(min_value=1, max_value=20)
    chapter = serializers.CharField(required=False, allow_null=True, allow_blank=True)
class SubmitRequestSerializer(serializers.Serializer):
    # keys are question numbers ("0", "1", ...), values are the chosen option number
    answers = serializers.DictField(
        child=serializers.IntegerField(min_value=0, max_value=10)
    )
