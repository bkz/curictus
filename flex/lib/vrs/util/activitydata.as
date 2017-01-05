//////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2006-2011 Curictus AB.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
// FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
// DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////////

private function getActivityData():Object {
    //
    // The list of activity aliases below must match the ones in the
    // vrs.config.activities Python module!
    //
    // It might seem stupid to have a big list of all the keys instead of
    // generating them dynamically. We do this to to have our i18N toolchain
    // automatically pick up the identifiers when it scans the codebase for 
    // new strings. Sometimes being stupid wins.
    //
    // A table is autogenerated with the following keys for each activity:
    //
    //   $activity_%s_name
    //   $activity_%s_summary
    //   $activity_%s_desc
    //   $activity_%s_video_xml
    //
    //   To update the table when you add or remove an activity simply run:
    //
    //     python activities.py # In the vrs.config directory!
    //
    //   ...and replace the table below with the output.
    //

    return {
        // HGT Tests
        'neglecttest' : [_('$activity_neglecttest_name'), _('$activity_neglecttest_summary'), _('$activity_neglecttest_desc'), _('$activity_neglecttest_video_xml'), _('$activity_neglecttest_level_desc')],
        'point' : [_('$activity_point_name'), _('$activity_point_summary'), _('$activity_point_desc'), _('$activity_point_video_xml'), _('$activity_point_level_desc')],
        'precision_h' : [_('$activity_precision_h_name'), _('$activity_precision_h_summary'), _('$activity_precision_h_desc'), _('$activity_precision_h_video_xml'), _('$activity_precision_h_level_desc')],
        'precision_v' : [_('$activity_precision_v_name'), _('$activity_precision_v_summary'), _('$activity_precision_v_desc'), _('$activity_precision_v_video_xml'), _('$activity_precision_v_level_desc')],
        'tmt_a' : [_('$activity_tmt_a_name'), _('$activity_tmt_a_summary'), _('$activity_tmt_a_desc'), _('$activity_tmt_a_video_xml'), _('$activity_tmt_a_level_desc')],
        'tmt_b' : [_('$activity_tmt_b_name'), _('$activity_tmt_b_summary'), _('$activity_tmt_b_desc'), _('$activity_tmt_b_video_xml'), _('$activity_tmt_b_level_desc')],
        // HGT Games
        'archery2' : [_('$activity_archery2_name'), _('$activity_archery2_summary'), _('$activity_archery2_desc'), _('$activity_archery2_video_xml'), _('$activity_archery2_level_desc')],
        'bandit' : [_('$activity_bandit_name'), _('$activity_bandit_summary'), _('$activity_bandit_desc'), _('$activity_bandit_video_xml'), _('$activity_bandit_level_desc')],
        'bingo2' : [_('$activity_bingo2_name'), _('$activity_bingo2_summary'), _('$activity_bingo2_desc'), _('$activity_bingo2_video_xml'), _('$activity_bingo2_level_desc')],
        'codebreak' : [_('$activity_codebreak_name'), _('$activity_codebreak_summary'), _('$activity_codebreak_desc'), _('$activity_codebreak_video_xml'), _('$activity_codebreak_level_desc')],
        'colors' : [_('$activity_colors_name'), _('$activity_colors_summary'), _('$activity_colors_desc'), _('$activity_colors_video_xml'), _('$activity_colors_level_desc')],
        'fishtank2' : [_('$activity_fishtank2_name'), _('$activity_fishtank2_summary'), _('$activity_fishtank2_desc'), _('$activity_fishtank2_video_xml'), _('$activity_fishtank2_level_desc')],
        'intro' : [_('$activity_intro_name'), _('$activity_intro_summary'), _('$activity_intro_desc'), _('$activity_intro_video_xml'), _('$activity_intro_level_desc')],
        'math2' : [_('$activity_math2_name'), _('$activity_math2_summary'), _('$activity_math2_desc'), _('$activity_math2_video_xml'), _('$activity_math2_level_desc')],
        'memory' : [_('$activity_memory_name'), _('$activity_memory_summary'), _('$activity_memory_desc'), _('$activity_memory_video_xml'), _('$activity_memory_level_desc')],
        'pong' : [_('$activity_pong_name'), _('$activity_pong_summary'), _('$activity_pong_desc'), _('$activity_pong_video_xml'), _('$activity_pong_level_desc')],
        'racer' : [_('$activity_racer_name'), _('$activity_racer_summary'), _('$activity_racer_desc'), _('$activity_racer_video_xml'), _('$activity_racer_level_desc')],
        'simon2' : [_('$activity_simon2_name'), _('$activity_simon2_summary'), _('$activity_simon2_desc'), _('$activity_simon2_video_xml'), _('$activity_simon2_level_desc')],
        'slotmachine' : [_('$activity_slotmachine_name'), _('$activity_slotmachine_summary'), _('$activity_slotmachine_desc'), _('$activity_slotmachine_video_xml'), _('$activity_slotmachine_level_desc')],
        // Deleted HGT Tests
        'tmt' : [_('$activity_tmt_name'), _('$activity_tmt_summary'), _('$activity_tmt_desc'), _('$activity_tmt_video_xml'), _('$activity_tmt_level_desc')],
        // Deleted HGT Games
        'slots' : [_('$activity_slots_name'), _('$activity_slots_summary'), _('$activity_slots_desc'), _('$activity_slots_video_xml'), _('$activity_slots_level_desc')],
        // Legacy Games
        'archery' : [_('$activity_archery_name'), _('$activity_archery_summary'), _('$activity_archery_desc'), _('$activity_archery_video_xml'), _('$activity_archery_level_desc')],
        'fishtank' : [_('$activity_fishtank_name'), _('$activity_fishtank_summary'), _('$activity_fishtank_desc'), _('$activity_fishtank_video_xml'), _('$activity_fishtank_level_desc')],
        'mugmastermind' : [_('$activity_mugmastermind_name'), _('$activity_mugmastermind_summary'), _('$activity_mugmastermind_desc'), _('$activity_mugmastermind_video_xml'), _('$activity_mugmastermind_level_desc')],
        // Deleted Legacy Games
        'bingo' : [_('$activity_bingo_name'), _('$activity_bingo_summary'), _('$activity_bingo_desc'), _('$activity_bingo_video_xml'), _('$activity_bingo_level_desc')],
        'math' : [_('$activity_math_name'), _('$activity_math_summary'), _('$activity_math_desc'), _('$activity_math_video_xml'), _('$activity_math_level_desc')],
        'memory' : [_('$activity_memory_name'), _('$activity_memory_summary'), _('$activity_memory_desc'), _('$activity_memory_video_xml'), _('$activity_memory_level_desc')],
        'simon' : [_('$activity_simon_name'), _('$activity_simon_summary'), _('$activity_simon_desc'), _('$activity_simon_video_xml'), _('$activity_simon_level_desc')]
    }
}

public function getActivityName(alias:String): String {
    return getActivityData()[alias][0];
}

public function getActivityDescSummary(alias:String): String {
    return getActivityData()[alias][1];
}
public function getActivityDesc(alias:String): String {
    return getActivityData()[alias][2];
}

public function getActivityVideoXML(alias:String): String {
    return getActivityData()[alias][3];
}