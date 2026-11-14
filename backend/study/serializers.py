from rest_framework import serializers


class DocumentIdsSerializer(serializers.Serializer):
    """Accepts document_ids (list) or the old single document_id."""
    document_id = serializers.IntegerField(required=False)
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        min_length=1,
        max_length=10,
        help_text="Ids of the selected files, in the same order as the UI shows them.",
    )

    def validate(self, attrs):
        ids = attrs.get("document_ids")
        if not ids:
            single = attrs.get("document_id")
            if single is None:
                raise serializers.ValidationError(
                    "Send document_ids (or document_id)."
                )
            ids = [single]
        # remove duplicates, keep the order
        attrs["ids"] = list(dict.fromkeys(ids))
        return attrs


class ChatRequestSerializer(DocumentIdsSerializer):
    question = serializers.CharField(max_length=2000)


class GenerateRequestSerializer(DocumentIdsSerializer):
    question_type = serializers.ChoiceField(choices=["mcq", "short", "long", "mixed"])
    difficulty = serializers.ChoiceField(choices=["low", "medium", "high"])
    count = serializers.IntegerField(min_value=1, max_value=20)
    chapter = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class SubmitRequestSerializer(serializers.Serializer):
    # keys are question numbers ("0", "1", ...), values are the chosen option number
    answers = serializers.DictField(
        child=serializers.IntegerField(min_value=0, max_value=10)
    )