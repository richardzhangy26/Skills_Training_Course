#url
https://cloudapi.polymas.com/teacher-course/abilityTrain/editScriptStepFlow

#method 
post

#payload
{
    "trainTaskId": "BJDw9PO5kWfY213AOdRO",
    "flowId": "PLmig6oXOkFE_fbAN_84H",
    "scriptStepStartId": "pc37S-RZx603eB0jP8XDW",
    "scriptStepStartHandle": "pc37S-RZx603eB0jP8XDW-source-bottom",
    "scriptStepEndId": "wxjtUCmrSMROHRB_BUSYg",
    "scriptStepEndHandle": "wxjtUCmrSMROHRB_BUSYg-target-top",
    "flowSettingType": "configuration",
    "flowCondition": "Situation 2 - Campus Part-Time Job Recommendation",
    "flowConfiguration": {
        "relation": "and",
        "conditions": [
            {
                "text": "条件组1",
                "relation": "and",
                "conditions": [
                    {
                        "text": "condition1 "
                    },
                    {
                        "text": "or "
                    }
                ],
                "isEdit": false
            },
            {
                "text": "条件组2",
                "relation": "and",
                "conditions": [
                    {
                        "text": "condition 21"
                    }
                ],
                "isEdit": false
            }
        ]
    },
    "transitionPrompt": "",
    "transitionHistoryNum": 10,
    "isDefault": 1,
    "isError": false
}

#response
{
    "code": 200,
    "msg": null,
    "data": {
        "trainTaskId": "BJDw9PO5kWfY213AOdRO",
        "flowId": "PLmig6oXOkFE_fbAN_84H",
        "scriptStepStartId": "pc37S-RZx603eB0jP8XDW",
        "scriptStepEndId": "wxjtUCmrSMROHRB_BUSYg",
        "scriptStepStartHandle": "pc37S-RZx603eB0jP8XDW-source-bottom",
        "scriptStepEndHandle": "wxjtUCmrSMROHRB_BUSYg-target-top",
        "flowCondition": "Situation 2 - Campus Part-Time Job Recommendation",
        "flowConfiguration": {
            "relation": "and",
            "conditions": [
                {
                    "text": "条件组1",
                    "relation": "and",
                    "conditions": [
                        {
                            "text": "condition1 "
                        },
                        {
                            "text": "or "
                        }
                    ],
                    "isEdit": false
                },
                {
                    "text": "条件组2",
                    "relation": "and",
                    "conditions": [
                        {
                            "text": "condition 21"
                        }
                    ],
                    "isEdit": false
                }
            ]
        },
        "isDefault": 1,
        "flowSettingType": "configuration",
        "transitionPrompt": "",
        "transitionHistoryNum": 10
    },
    "currentTime": 1781154521000,
    "traceId": "8096df177eaa4fd19d59ae4be0026349",
    "success": true
}