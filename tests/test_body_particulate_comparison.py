from tools.geometry.compare_particulate_to_body_architecture import (
    compare_particulate,
)


def conditioning():
    return {
        "architecture_id":"test",
        "component_plan":{
            "generated_component_slots":[
                {"slot_id":"torso_shell","required":True},
                {"slot_id":"arm_l_shell","required":True},
            ],
            "joint_component_bindings":[
                {
                    "joint_id":"shoulder_l",
                    "parent_slot":"torso_shell",
                    "child_slot":"arm_l_shell",
                    "binding_status":"inter_component",
                },
                {
                    "joint_id":"elbow_l",
                    "parent_slot":"arm_l_shell",
                    "child_slot":"arm_l_shell",
                    "binding_status":"within_combined_component_slot",
                },
            ],
        },
        "skeleton_control":{
            "nodes":{
                "shoulder_l":{"position_mm_at_target_height":[0,0,0]}
            },
            "joints":[
                {
                    "joint_id":"shoulder_l",
                    "joint_type":"revolute",
                    "parent_node":"shoulder_l",
                    "child_node":"tip",
                    "axis":[1,0,0],
                    "range_deg":[-90,90],
                }
            ],
        },
    }


def critic():
    return {
        "critic_id":"particulate",
        "parts":[
            {
                "part_id":0,"motion_class":"fixed_or_unclassified",
                "revolute_axis_direction":[1,0,0],
                "revolute_axis_point_in_prediction_frame":[0,0,0],
                "revolute_range_radians":[0,0],
            },
            {
                "part_id":1,"motion_class":"revolute",
                "revolute_axis_direction":[1,0,0],
                "revolute_axis_point_in_prediction_frame":[0,0,0],
                "revolute_range_radians":[-1.57079632679,1.57079632679],
            },
        ],
        "motion_hierarchy":[[0,1]],
    }


def proposal():
    return {
        "global_alignment_candidates":[
            {
                "total_score":0,
                "complete_required_visual_mapping":True,
                "global_transform_particulate_to_brickmen_mm":[
                    1,0,0,0,
                    0,1,0,0,
                    0,0,1,0,
                    0,0,0,1,
                ],
                "assignments":[
                    {"particulate_part_id":0,"slot_id":"torso_shell"},
                    {"particulate_part_id":1,"slot_id":"arm_l_shell"},
                ],
            }
        ]
    }


def test_particulate_comparison_matches_component_graph_and_axis():
    result=compare_particulate(
        conditioning(),critic(),proposal(),0
    )
    graph=result["graph_comparison"]
    assert graph["matched_pairs"]==[["arm_l_shell","torso_shell"]]
    assert graph["missing_expected_pairs"]==[]
    obs=result["joint_observations"][0]
    assert obs["expected_joint_id"]=="shoulder_l"
    assert obs["axis_direction_error_deg_sign_invariant"]==0
    assert abs(obs["range_span_error_deg"])<1e-6
    assert graph["within_combined_slot_joints_not_expected_as_separate_parts"][0]["joint_id"]=="elbow_l"
