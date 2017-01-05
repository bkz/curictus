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

import flash.net.SharedObject;
import flash.net.URLRequest;
import flash.system.Capabilities;
import flash.system.fscommand;

import mx.collections.Sort;
import mx.collections.SortField;
import mx.collections.ArrayCollection;
import mx.utils.ObjectUtil;

import mx.controls.Alert;
import mx.events.ListEvent;
import mx.utils.ObjectProxy;
import mx.utils.UIDUtil;

import mx.managers.PopUpManager;
import mx.printing.FlexPrintJobScaleType;

import mx.managers.BrowserManager;
import mx.managers.IBrowserManager;
import mx.events.BrowserChangeEvent;

import vrs.PCMService;
import vrs.shared.Activity;
import vrs.shared.ActivityInfo;
import vrs.shared.ActivityType;
import vrs.shared.Patient;
import vrs.shared.Session;
import vrs.shared.Zone;
import vrs.system.SystemInfo;

import CustomFlexPrintJob;
import PrintHelpDialog;

private const FORCE_SCROLLBAR_MIN_WIDTH:int = 1100;
private const FORCE_SCROLLBAR_MIN_HEIGHT:int = 500;

[Bindable] public var selectedZone:Zone= null;
[Bindable] public var selectedPatient:Patient = null;
[Bindable] public var selectedActivity:Activity = null;

public var pcmsService:PCMService = new PCMService;

private var browserManager:IBrowserManager;

public function init():void {
    pcmsService.connect(Application.application.getServerURL() + "pcms/amf/", pcmExceptionHandler);
    
    browserManager = BrowserManager.getInstance();
    // FIXME: Why doesn't the browser title change (tested in Chrome)?
    browserManager.init("", _('Curictus PCMS - Loading...'));
}

public function complete():void {
    browserManager.setTitle(_('Curictus PCMS'));
        
    pcmsService.getSystemLangCode(       
        function(langCode:String):void {
            pcmsService.getTranslations(langCode,
                function(table:ObjectProxy):void {
                    GetText.getInstance().changeLanguage(table);
                    currentState = 'loginState';
                    visible = true;
                });
        });
        
    // Load zones into login form
    pcmsService.listZones(
        function(result:ArrayCollection):void {
            loginComponent.zoneComboBox.dataProvider = result;
            // Simulate a blank entry in combobox, so user is forced to make an active choice.
            loginComponent.zoneComboBox.selectedIndex = -1;
            loginComponent.refresh();
        });
}

public function pcmExceptionHandler(method:String, type:String, message:String):void {
    Alert.show(
        _("Don't worry, we'll help you. Please contact Curictus Support (www.curictus.com/support).\n\nWrite down or take a photo of this message:") +
            "\n\n" + type + " in " + method + " (" + message + ")",
        
        _('Oops! Something went wrong.')
    );
}

public function setLangauge(lang:String):void {
    pcmsService.getTranslations(lang, 
        function(table:ObjectProxy):void {
            GetText.getInstance().changeLanguage(table);
        });
}

public function logout():void {
    navigateToURL(new URLRequest(Application.application.url), '_self');

}

public function login(zone:Zone, password:String):void {
    this.selectedZone = zone;
    if (this.selectedZone != null) {       
        //
        // Rate-limit logins on the basis of failed attempts. We don't bother with
        // tracking IP:s or other expensive stuff at the application layer for two
        // important reasons:
        // 
        // 1. Our customers will most likely be behind proxies.
        // 2. Brute force protection/filtering is better handled at the packet level 
        //    using IPTables instead of doing stuff manually at the HTTP/RPC level.
        // 
        // Security is offloaded to SSL/HTTPS so our only responsibility at the client
        // level is to obfuscate stuff a bit to slow down script kiddies. We do so by
        // simply tracking failed consecutive login attempts and lock out users out for 
        // a while which aren't behaving normally.
        //
        // NOTE: we're using plain insecure Flash cookie storage for storing state, 
        // most people who can cirument this will easily break anything else we do at 
        // the client side (other than SSL). No point in being clever.
        // 
        
        const DEFAULT_LOGIN_TICKETS:uint = 10;
        const MAX_TICKETS_AFTER_LOCKED_OUT:uint = 3;
        const LOCKED_OUT_WAIT_TIME_MS:Number = 5 * 60 * 1000;
        
        var so:SharedObject = SharedObject.getLocal("pcms");

        if (!so.data.hasOwnProperty("login_date"))
            so.data.login_date = new Date();        
        if (!so.data.hasOwnProperty("login_tokens"))
            so.data.login_tokens = DEFAULT_LOGIN_TICKETS;
        if (!so.data.hasOwnProperty("login_uuid"))
            so.data.login_uuid = UIDUtil.createUID();
            
        var lockedOut:Boolean = !so.data.login_tokens;
        
        var elapsedMs:Number = (new Date().getTime() - so.data.login_date.getTime());       
        if (lockedOut && elapsedMs > LOCKED_OUT_WAIT_TIME_MS) {
            so.data.login_date = new Date();        
            so.data.login_tokens = MAX_TICKETS_AFTER_LOCKED_OUT;
            so.flush();            
            lockedOut = false;
        }
                
        if (lockedOut) {                       
            var timeLeftMin:Number = Math.ceil((LOCKED_OUT_WAIT_TIME_MS - elapsedMs) / 1000 / 60);
            loginComponent.lockedOut(timeLeftMin);
        }
        else {
            pcmsService.authenticate(zone.guid, password, 
                function(ok:Boolean):void {                
                    if (ok) {
                        so.data.login_date = new Date();
                        so.data.login_tokens = DEFAULT_LOGIN_TICKETS;
                        so.flush();                        
                        
                        // NOTE: this is a crazy work-around to force Flex to enable scrollbars when our 
                        // application can't automatically resize and rescale properly. You would think 
                        // that settings these values on Application.application would work but no, you 
                        // need to limit the actual object intended to be scrolled. Be advised, don't try 
                        // any JS/ExternalInterface tricks using libraries like swffit (IE8-9 break) - 
                        // simply force the browser to always hide it's scrollbars and let Flex renders 
                        // its own ones.
                        //
                        // We can't do this before the user has logged in since we want the login screen to 
                        // scale correctly and work in all resolutions. Yeah.
                        topViewStack.minWidth  = FORCE_SCROLLBAR_MIN_WIDTH;
                        topViewStack.minHeight = FORCE_SCROLLBAR_MIN_HEIGHT;
                        
                        currentState = 'mainState';
                    } else {
                        so.data.login_date = new Date();
                        so.data.login_tokens -= 1;
                        so.flush();
                        loginComponent.wrongPassword();
                    }        
                });
        }
    }
}

public function doubleClickSelectPatient():void {
	this.selectPatientHelper(this.selectUserComponent.dataGridPatients.selectedItem as Patient);
}
public function selectPatient(patient:Patient):void {
    if (patient != this.selectedPatient) {
		this.selectPatientHelper(patient);
	}
}
private function selectPatientHelper(patient:Patient):void {
	this.selectUserComponent.selectPatientButton.enabled = false;
	this.selectUserComponent.selectPatientButton.emphasized = false;
	
	this.activityReportComponent.enabled = true;
	this.activitiesComponent.enabled = true;
    this.dataAnalysisComponent.enabled = true;

	if (this.selectedPatient != null) {
		this.selectedPatient = patient;
		this.populateActivityReport();
	} else {
		this.selectedPatient = patient;
	}
	
    this.dataAnalysisComponent.refresh();
    
	this.mainViewStack.selectedChild = this.activityReportComponent;
    
    stats.track('select-patient', { 'zone':selectedZone.alias } );
}

public function populatePatientList():void {
    pcmsService.listPatients(this.selectedZone, 
        function(result:ArrayCollection):void {
            //Alert.show('length=' + result.length);
            selectUserComponent.dataGridPatients.dataProvider = result;
            selectUserComponent.dataGridPatients.selectedIndex = -1;
        });
}

public function populateActivities():void {
    pcmsService.listActivities(
        function(result:ArrayCollection):void {
            activitiesComponent.dataGrid.dataProvider = result;
            
            // Sort activities list by category (assessments first) and then by alias.
            var sortField:SortField = new SortField;
            sortField.compareFunction = function(a:ActivityInfo, b:ActivityInfo):int {
                if (a.kind !== b.kind) {
                    if (a.kind == "test")
                        return -1;
                    else 
                        return 1;
                }
                
                return ObjectUtil.stringCompare(getActivityName(a.alias), getActivityName(b.alias));
            }
            
            var sort:Sort = new Sort;
            sort.fields = [sortField];
            
            activitiesComponent.dataGrid.dataProvider.sort = sort;
            activitiesComponent.dataGrid.dataProvider.refresh();
            activitiesComponent.dataGrid.selectedIndex = -1;
        });
}

public function populateActivityReport():void {
    pcmsService.groupSessionsByDay(selectedPatient, "*", 14,
        function(result:ArrayCollection):void {
            var data:Array = [];
            
            for (var i:int = 0; i < result.length; i++)
            {
                var group:Object = result.getItemAt(i);
                        
                var last:Session = null;
                
                if (group.sessions.length > 0)
                {
                    for (var j:int = 0; j < group.sessions.length; j++)
                    {
                        var s:Session = group.sessions.getItemAt(j) as Session;
                                               
                        if (last)
                        {
                            const PAUSE_MIN_LIMIT_SEC:int = 4 * 60;
                                                        
                            var diff_t:int = (s.timestamp.getTime() - last.timestamp.getTime()) / 1000;
                            
                            if (diff_t > PAUSE_MIN_LIMIT_SEC)
                            {
                               data.push({ kind: "pause", duration: diff_t}); 
                            }
                        }
                        
                        last = s;
                        
                        data.push({ kind: "session", date: group.date, session: s});
                    }                        
                }
                
                data.push({ kind: "weekday", date: group.date, session_count: group.sessions.length });                
            }       
            
            data.reverse();
                             
            activityReportComponent.overviewDataGrid.dataProvider = new ArrayCollection(data);
            activityReportComponent.overviewDataGrid.dataProvider.refresh();
        });
		
		// TODO: Move...
		this.updatePatientView();
}

public function saveMedicalRecord(record:ObjectProxy):void {
    pcmsService.saveMedicalRecord(this.selectedPatient, record);
}

public function updatePatientView():void
{
    activityReportComponent.activityReportTabNavigator.selectedIndex = 0;
    
	/*
	pcmsService.findSessions(selectedPatient,
		function(result:ArrayCollection):void {
			dataGridSessions.dataProvider = result;
		});
	*/
	
	pcmsService.groupSessionsByDay(selectedPatient, "point", 0,
		function(result:ArrayCollection):void {
			//debugMessages.text += "---------------------------------------------------\n"                                                        
			//debugMessages.text += "Grouping all patient point-tests:\n";
			
			var chartData:Array = [];
			
			for (var i:int = 0; i < result.length; i++)
			{
				var group:Object = result.getItemAt(i);
				
				//debugMessages.text += "Date:" + group.date + "\n";
				
				var bestSession:Session = null;
				
				if (group.sessions.length > 0)
				{
					for (var j:int = 0; j < group.sessions.length; j++)
					{
						var s:Session = group.sessions.getItemAt(j) as Session;
						
						//debugMessages.text += " -> " +  s.activity.alias + " " + s.timestamp + "(assessment duration:" + int(s.score.duration) + " session duration: " + s.duration + ")\n";
						
						if (s.score.duration > 0 && (!bestSession || s.score.duration < bestSession.score.duration))
							bestSession = s
					}                                
				}
				else
				{
					//debugMessages.text += " -> empty!\n";
				}
				
				if (bestSession)
				{
					//debugMessages.text += " -> selecting best session:" + bestSession.timestamp + "\n";
					chartData.push( { date: group.date, duration: int(bestSession.score.duration) } );                                
				}
				else
				{
					//debugMessages.text += " -> no valid session found!\n";
				}
			}                              
							 
			activityReportComponent.pointTestChart.dataProvider = new ArrayCollection(chartData);
		});
			
	pcmsService.groupSessionsByDay(selectedPatient, "*", 14,
		function(result:ArrayCollection):void {
			
			var chartData:Array = [];
			
			for (var i:int = 0; i < result.length; i++)
			{
				var group:Object = result.getItemAt(i);
				
				var sumDuration:int = 0;
				
				if (group.sessions.length > 0)
				{
					for (var j:int = 0; j < group.sessions.length; j++)
					{
						var s:Session = group.sessions.getItemAt(j) as Session;
						
						sumDuration += s.duration;
					}                                
				}
				else
				{
					//debugMessages.text += " -> empty!\n";
				}
				
				chartData.push( { date: group.date, duration: Math.ceil(sumDuration / 60) } );                            
			}                           

			activityReportComponent.dayReportChart.dataProvider = new ArrayCollection(chartData);
		})    
		
	pcmsService.groupSessionsByWeek(selectedPatient, "*", 24,
		function(result:ArrayCollection):void {
			//debugMessages.text += "---------------------------------------------------\n"                            
			//debugMessages.text += "Grouping all sessions from last 24 weeks:\n";
			
			var chartData:Array = [];
									 
			for (var i:int = 0; i < result.length; i++)
			{
				var group:Object = result.getItemAt(i);
				
				//debugMessages.text += "Date:" + group.date + "\n";
				//debugMessages.text += "Week:" + group.week + "\n";
				
				var sumDuration:int = 0;
				
				if (group.sessions.length > 0)
				{
					for (var j:int = 0; j < group.sessions.length; j++)
					{
						var s:Session = group.sessions.getItemAt(j) as Session;
						
						//debugMessages.text += " -> " +  s.activity.alias + " " + s.timestamp + " " + int(s.duration) + "\n";
						
						sumDuration += s.duration;
					}                                
				}
				else
				{
					//debugMessages.text += " -> empty!\n";
				}
				
				chartData.push( { date: group.date, week: group.week, duration: Math.ceil(sumDuration / 60) } );                            
			}                           

			activityReportComponent.weekReportChart.dataProvider = new ArrayCollection(chartData);
		})                             
		
	pcmsService.groupSessionsByMonth(selectedPatient, "*", 12,
		function(result:ArrayCollection):void {
			//debugMessages.text += "---------------------------------------------------\n"                            
			//debugMessages.text += "Grouping all sessions from last 6 months:\n";
			
			var chartData:Array = [];
									 
			for (var i:int = 0; i < result.length; i++)
			{
				var group:Object = result.getItemAt(i);
				
				//debugMessages.text += "Date:" + group.date + "\n";
				
				var sumDuration:int = 0;
				
				if (group.sessions.length > 0)
				{
					for (var j:int = 0; j < group.sessions.length; j++)
					{
						var s:Session = group.sessions.getItemAt(j) as Session;
						
						//debugMessages.text += " -> " +  s.activity.alias + " " + s.timestamp + " " + int(s.duration) + "\n";
						
						sumDuration += s.duration;
					}                                
				}
				else
				{
					//debugMessages.text += " -> empty!\n";
				}
				
				chartData.push( { date: group.date, duration: Math.ceil(sumDuration / 60) } );                            
			}                           

			
			activityReportComponent.monthReportChart.dataProvider = new ArrayCollection(chartData);
		})
	
}

public function printPage():void
{
    var printer:CustomFlexPrintJob = new CustomFlexPrintJob();
    
    if (printer.start() == true)
    {
        if (printer.printJob.orientation != PrintJobOrientation.LANDSCAPE)
        {
            var dialog :PrintHelpDialog;
            dialog = new PrintHelpDialog();
            PopUpManager.addPopUp(dialog, this, true);
            PopUpManager.centerPopUp(dialog);
        }
        else
        {                   
            printer.addObject(mainComponent, FlexPrintJobScaleType.SHOW_ALL);                     
        }
        
        printer.send();                 
    }       
}