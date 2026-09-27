import pytest

from tools.geometry.build_pact_semantic_mask_editor import (
    build_pact_mask_editor_html,
)


def conditioning():
    return {
        "architecture_id":"giant",
        "target_height_mm":62,
        "component_plan":{
            "generated_component_slots":[
                {"slot_id":"torso_shell","role":"torso","required":True},
                {"slot_id":"arm_l_shell","role":"arm","side":"left","required":True},
                {"slot_id":"arm_r_shell","role":"arm","side":"right","required":True},
            ]
        },
    }


def test_semantic_mask_editor_embeds_slot_legend_not_source_image():
    page=build_pact_mask_editor_html(conditioning())
    assert "Brickmen PAct Semantic Mask Editor" in page
    assert '"label":1,"slot_id":"torso_shell"' in page
    assert '"label":2,"slot_id":"arm_l_shell"' in page
    assert '"label":3,"slot_id":"arm_r_shell"' in page
    assert 'type="file" accept="image/*"' in page
    assert "source_image_embedded:false" in page
    assert "data:image/" not in page


def test_semantic_mask_editor_requires_slots():
    with pytest.raises(ValueError,match="no generated component slots"):
        build_pact_mask_editor_html({"architecture_id":"empty"})
