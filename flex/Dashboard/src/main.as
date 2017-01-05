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

﻿import flash.events.Event;
import flash.events.TimerEvent;
import flash.media.*;
import flash.system.Capabilities;
import flash.system.fscommand;
import flash.utils.Timer;
import mx.collections.ArrayCollection;
import mx.controls.Alert;
import mx.core.IFlexDisplayObject;
import mx.core.SoundAsset;
import mx.events.ListEvent;
import mx.managers.PopUpManager;
import mx.rpc.events.FaultEvent;
import mx.rpc.events.ResultEvent;
import mx.utils.ObjectProxy;

import flash.ui.Keyboard;
import flash.events.KeyboardEvent;

import vrs.DashboardService;
import vrs.shared.Activity;
import vrs.shared.Patient;
import vrs.shared.Session;
import vrs.system.SystemInfo;

public var currentActivityId:String = null;
public var dashboardService:DashboardService = new DashboardService;
public var selectedActivity:Activity = null;
public var selectedPatient:Patient = null;
public var featureFlags:ObjectProxy = null;

// Embedded sounds
[Embed(source="assets/sounds/startup.mp3")]
[Bindable]
public static var startupSound:Class;
public var startupSoundAsset:SoundAsset;

[Embed(source="assets/sounds/blip.mp3")]
[Bindable]
public static var defaultSound:Class;
public var defaultSoundAsset:SoundAsset;

[Embed(source="assets/sounds/click.mp3")]
[Bindable]
public static var clickSound:Class;
public var clickSoundAsset:SoundAsset;

[Embed(source="assets/sounds/good_result.mp3")]
[Bindable]
public static var goodResultSound:Class;
public var goodResultSoundAsset:SoundAsset;

// Timers
public var abortionTimer:Timer;
public var periodicTimer:Timer;

///////////////////////////////////////////////////////////////////////////////////////
// Initialization.
///////////////////////////////////////////////////////////////////////////////////////

private function init():void {   
    // Connect to dashboard service
    dashboardService.connect(DASHBOARD_ADDRESS + "dashboard/amf/", dashboardExceptionHandler, false);
    
    // Initialize sounds
    this.defaultSoundAsset = new defaultSound() as SoundAsset;
    this.startupSoundAsset = new startupSound() as SoundAsset;
    this.clickSoundAsset = new clickSound() as SoundAsset;  
    this.goodResultSoundAsset = new goodResultSound() as SoundAsset;
	
    // Set master volume
	SoundMixer.soundTransform = new SoundTransform(0.4);
	
    // Start abortion timer
    abortionTimer = new Timer(60 * 10 * 1000, 1); // Runs only once
    abortionTimer.addEventListener(TimerEvent.TIMER, this.abortDashboard);
    abortionTimer.start();
    
    // Start periodic timer
    periodicTimer= new Timer(5 * 1000, 0); // Runs indefintely
    periodicTimer.addEventListener(TimerEvent.TIMER, this.periodicUpdate);
    periodicTimer.start();
    
    dashboardService.getFeatureFlags(
        function(config:ObjectProxy): void {
            featureFlags = config;
            
            if (featureFlags["enable_tilted_frame"])
            {
                dashboardContainer.setStyle("paddingTop", 100);
            }
        })
        
    this.systemManager.stage.addEventListener(KeyboardEvent.KEY_DOWN, 
        function (e:KeyboardEvent):void {
             if (e.keyCode == Keyboard.BACKSPACE) {
                currentState = 'systemMenuState';
             }
        });
            
    // Setup activity information screens
    this.preActivityComp.setActivityType('game');
    this.preAssessmentComp.setActivityType('test');

}

private function complete():void {
    dashboardService.getSystemBuild(
        function(v:String):void {
            versionLabel.text = _("Version") + " " + v;
        });
            
    {
        const WAIT_MS_BETWEEN_CHECK:int = 15*1000;
        const MAX_FAILURES_IN_ROW:int = 4;
        
        var failureCount:int = 0;
        
        setInterval(        
            function():void {
                // Note: Offline standalone system don't require working network access.
                if (!featureFlags["enable_standalone_mode"]) {
                    dashboardService.haveNetworkAccess(
                        function(yes:Boolean):void {
                            if (yes) {
                                failureCount = 0;
                                notificationLabel.text = "";
                                notificationLabel.visible = false;
                            }
                            else {
                                failureCount += 1;
                                if (failureCount == MAX_FAILURES_IN_ROW) {
                                    notificationLabel.text = _("Internet connection not available, please inform the IT department.");
                                    notificationLabel.visible = true;                                
                                }
                            }
                        })
                }
            }
        ,
        WAIT_MS_BETWEEN_CHECK);
    }
    

    dashboardService.getTranslations(
        function(table:ObjectProxy):void {
            GetText.getInstance().changeLanguage(table);
            startup();
        });
}


///////////////////////////////////////////////////////////////////////////////////////
// Startup logic.
///////////////////////////////////////////////////////////////////////////////////////

private function startup():void {
    this.currentState = "emptyState";
    this.visible = true;
    
    dashboardService.isPatientLoggedIn(
        function(loggedIn:Boolean):void { 
            if (loggedIn) {
                startupLoggedIn();
            } else {                
                if (featureFlags["enable_demo_mode"]) {
                    loginAsGuest();
                }
                else {
                    currentState = 'initMenuState'; // Not logged in;
                }
            }
        });       
}

private function startupLoggedIn():void {
    dashboardService.hasNewSession(
        function(available:Boolean):void {
            if (available) {
                startupSessionAvailable();
            } else {
                // No new session - show main menu.
                showMainMenu();
            }
        });
}

private function startupSessionAvailable():void {
    dashboardService.getLastSession(
        function(session:Session):void {
            // New session available, show activity info screen.
			setActivityResults(session.activity.alias, session);
            updateMainMenu();
            updateMainMenuUser();
        });							
}

///////////////////////////////////////////////////////////////////////////////////////
// 
///////////////////////////////////////////////////////////////////////////////////////
public var dashboardHelp:DashboardHelp;

public function showHelp(msg:String, doneCallback:Function = null):void {
    dashboardHelp = new DashboardHelp();
    dashboardHelp.helpText = msg;
    dashboardHelp.callback = doneCallback;
    PopUpManager.addPopUp(dashboardHelp, this, true);
    PopUpManager.centerPopUp(dashboardHelp);
}


public function setCurrentActivity(id:String):void {
    dashboardService.getActivityKind(id,
        function(kind:String):void {
            currentActivityId = id;
        
            if (kind == 'test') {
                preAssessmentComp.setActivity(currentActivityId);
                currentState = 'preAssessmentState'
            } else {
                preActivityComp.setActivity(currentActivityId);
                currentState = 'preActivityState';
            }
        });
}

public function setActivityResults(id:String, s:Session):void {
    dashboardService.getActivityKind(id,
        function(kind:String):void {
            currentActivityId = id;    
            
            if (kind == 'test') {
                preAssessmentComp.setActivity(currentActivityId);
                preAssessmentComp.setResults(s);
                currentState = 'preAssessmentState';
                goodResultSoundAsset.play();
            } else {
                preActivityComp.setActivity(currentActivityId);
                preActivityComp.setResults(s);
                currentState = 'preActivityState';
                goodResultSoundAsset.play();
            }            
        });            
}


public function periodicUpdate(event:TimerEvent):void {
    this.updateMainMenu();
}

public function updateMainMenu():void {
}

public function updateMainMenuUser():void {
    dashboardService.isPatientLoggedIn(
        function(loggedIn:Boolean):void { 
            if (loggedIn) {
                dashboardService.getCurrentPatient(
                    function(p:Patient):void {
                        mainMenuComp.update(p);
                    });            
            }
        });
}

public function showMainMenu():void {
    this.updateMainMenu();
    this.updateMainMenuUser();
    currentState = 'mainMenuState';
    startupSoundAsset.play();
}

public function setLanguageCode(c:String):void {
    dashboardService.setLanguageCode(c,
        function(b:Boolean):void {
            dashboardService.getTranslations(
                function(table:ObjectProxy):void {
                    GetText.getInstance().changeLanguage(table);
                });            
        });        
}

// Receives an event each time a new state is entered.
// Resets abortion timer.
public function stateEntered(event:Event):void {
    this.abortionTimer.reset();
    this.abortionTimer.start();
    //trace ("enterState" + event);
}

///////////////////////////////////////////////////////////////////////////////////////
// Dashboard service calls.
///////////////////////////////////////////////////////////////////////////////////////

public function abortDashboard(event:TimerEvent):void {
    trace('Abortion timer logging out and sending fscommand("abort_h3d")');
    dashboardService.reset(
        function(b:Boolean):void {						
            if (b) {
                currentState = 'exitState';
                fscommand("abort_h3d");
            }
        });
}

public function exitDashboard():void
{
    if (Capabilities.playerType == "StandAlone")
    {
        currentState = 'exitState';
        fscommand("quit"); 
    }
    else 
    {
        // We're either running as a FlashMovieTexture in H3D or in a browser in 
        // which case we can't do anything. We'll just simply assume we can communicate 
        // with a H3D host and hope for the best :)
        currentState = 'exitState';
        fscommand("quit_h3d"); 
    }
}


public function checkNewPincode(pincode:String):void
{                   
    dashboardService.isPincodeInUse(pincode, 
        function(b:Boolean):void {
            if (!b) {
                createUserComp.enableUserCreate();
                createUserComp.loginMessage.text = _("Thanks. Now press 'Create Profile'.");
            } else {
                createUserComp.loginMessage.text = _("This PIN code is already in use.");
            }
        });
}


public function createNewLogin(pincode:String):void
{
    dashboardService.createNewLogin(pincode,
        function(b:Boolean):void {						
            // To keep the UI smooth we'll avoid introducing jerkiness as the system 
            // perform a rather compliated DB-query to sort the user list.
            setTimeout(function():void {
                loginComp.refresh();
            }, 250)
            
            showHelp(_('$dashboard_usercreated_help'),
                function():void {
                    // Don't reset the pincode as user will be able to see it in the background 
                    // as they read the hint. This useful if they want to want to write it down 
                    // and need to leave the station temporarily. 
                    createUserComp.resetLogin();
                    currentState = 'initMenuState';
                });
        });
}

public function loginAsGuest():void
{
    dashboardService.loginAsGuest(
        function(b:Boolean):void {
            showMainMenu();
        });				
}

public function loginWithPincode(pincode:String):void
{
    dashboardService.loginWithPincode(pincode,
        function(b:Boolean):void {			
            showMainMenu();
        });
}

public function logout():void
{
    dashboardService.logout(
        function(b:Boolean):void {						
            if (b) {
                exitDashboard();
            }
        });				
}

public function userLogout():void
{
    dashboardService.reset(
        function(b:Boolean):void {						
            if (b) {
                exitDashboard();
            }
        });				
}

public function terminate():void
{
    dashboardService.terminate(
        function(b:Boolean):void {						
            if (b) {
                exitDashboard();
            }
        });				
}
public function shutdown():void
{
    dashboardService.shutdown(
        function(b:Boolean):void {						
            if (b) {
                exitDashboard();
            }
        });				
}

public function launchGame():void
{
    dashboardService.launchGame(currentActivityId,
        function(ok:Boolean):void {						
            if (ok) {
                exitDashboard();
            }
        });		
}

public function launchTest():void
{
    dashboardService.launchTest(currentActivityId,
        function(ok:Boolean):void {						
            if (ok) {
                exitDashboard();
            }
        });		
}

public function updateSystemInfo():void {
    systemMenuComp.systemInfo.text = _('Please wait...');
    
    dashboardService.getSystemInfo(
        function(info:SystemInfo):void {
            systemMenuComp.systemInfo.text = '';
            systemMenuComp.systemInfo.text += "Station alias: " + info.station_alias + "\n";
            systemMenuComp.systemInfo.text += "VRS version: " + info.version + "\n";
            systemMenuComp.systemInfo.text += "Connected to Internet: " + info.connected_net + "\n\n";
            
            systemMenuComp.systemInfo.text += "Local IP: " + info.local_ip + "\n";
            systemMenuComp.systemInfo.text += "Public IP: " + info.public_ip + "\n";
            systemMenuComp.systemInfo.text += "OpenVPN IP: " + info.openvpn_ip + "\n\n";
            
            systemMenuComp.systemInfo.text += "Station guid: " + info.station_guid + "\n";
            systemMenuComp.systemInfo.text += "Zone guid: " + info.zone_guid + "\n";
            
        });
}

///////////////////////////////////////////////////////////////////////////////////////
// Exception handlers.
///////////////////////////////////////////////////////////////////////////////////////

public function dashboardExceptionHandler(method:String, type:String, message:String):void {
    Alert.show(
        _("Don't worry, we'll help you. Please contact Curictus Support (www.curictus.com/support). Tell them the following message:") +
            "\n\n" + type + " in " + method + " (" + message + ")",
        
        _('Oops! Something went wrong')
    );
}

