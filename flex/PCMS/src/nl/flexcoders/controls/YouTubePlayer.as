/**
 * YouTubePlayer!!!
 * 
 * Do you like it? Hate it? Please leave a comment.
 * And do whatever with it whatever you like.
 * 
 * 
 * Just Remember My Name: MAIKEL J. SIBBALD
 * LOL! I'm so Funny.
 * */
package nl.flexcoders.controls{
	import flash.display.Loader;
	import flash.display.Stage;
	import flash.display.StageDisplayState;
	import flash.events.FullScreenEvent;
	import flash.geom.Rectangle;
	import flash.net.URLRequest;
	import flash.utils.clearInterval;
	import flash.utils.setInterval;
	
	import mx.core.UIComponent;

	public class YouTubePlayer extends UIComponent{
		public static const PLAY_URL:String = "http://www.youtube.com/apiplayer?version=3";
		
		[Bindable]public var qualityLevels:Array = ["default", "small", "medium", "large", "hd720"]; 
		[Bindable]public var videoStates:Array = ["unstarted", "ended", "playing", "paused", "buffering", "video cued"]; 
		
		public var player:Object;
		
		private var loader:Loader = new Loader();
		
		private var _videoID:String = "";
		private var videoIDChanged:Boolean = false;
		
		private var _videoURL:String = "";
		private var videoURLChanged:Boolean = false;
		
		private var _volume:Number = 1;
		private var volumeChanged:Boolean = false;
		
		private var _duration:Number = 0;
		private var _currentTime:Number = 0;
		
		private var _autoPlay:Boolean = false;
		
		private var _playbackQuality:String = "default";
		private var playbackQualityChanged:Boolean = false;
		
		private var oldBounds:Rectangle;
		private var oldChildIndex:Number = -1;
		private var oldParent:*;
		
		[Bindable]
		public function set videoID(value:String):void{
			this._videoID = value;
			this.videoIDChanged = true;
			this.invalidateProperties();
		}
		
		public function get videoID():String{
			return this._videoID;
		}
		
		[Bindable]
		public function set videoURL(value:String):void{
			this._videoURL = value;
			this.videoURLChanged = true;
			this.invalidateProperties();
		}
		
		public function get videoURL():String{
			return this._videoURL;
		}
		
		[Bindable]
		public function set autoPlay(value:Boolean):void{
			this._autoPlay = value;
			this.invalidateProperties();
		}
		
		public function get autoPlay():Boolean{
			return this._autoPlay;
		}
		
		[Bindable]
		public function set playbackQuality(value:String):void{
			this._playbackQuality = value;
			this.playbackQualityChanged = true;
			this.invalidateProperties();
		}
		
		public function get playbackQuality():String{
			return this._playbackQuality;
		}
		
		[Bindable]
		public function set volume(value:Number):void{
			this._volume = value;
			this.volumeChanged = true;
			this.invalidateProperties();
		}
		
		public function get volume():Number{
			return this._volume;
		}
		
		[Bindable]
		public function set duration(value:Number):void{
			this._duration = value;
			this.invalidateProperties();
		}
		
		public function get duration():Number{
			return this._duration;
		}
		
		[Bindable]
		public function set currentTime(value:Number):void{
			this._currentTime = value;
			this.invalidateProperties();
		}
		
		public function get currentTime():Number{
			return this._currentTime;
		}
		
		public function get getPlaybackQuality():String{
			if(this.player){
				return player.getPlaybackQuality();
			}else{
				return "Not avaliable";
			}
		}
		
		public function get getAvailableQualityLevels():Array{
			if(this.player){
				return player.getAvailableQualityLevels();
			}else{
				return [];
			}
		}
		
		public function play():void{
			if(this.player){
				this.player.playVideo();
			}
		}
		public function pause():void{
			if(this.player){
				this.player.pauseVideo();
			}
		}
		public function stop():void{
			if(this.player){
				this.player.stopVideo();
			}
		}
		
		public function seekTo(seconds:Number, allowSeekAhead:Boolean = false):void{
			if(this.player){
				this.player.seekTo(seconds, allowSeekAhead);
			}
		}
		
		public function mute():void{
			if(this.player){
				this.player.mute();
			}
		}
		public function unMute():void{
			if(this.player){
				this.player.unMute();
			}
		}
		public function isMuted():Boolean{
			if(this.player){
				return this.player.isMuted();
			}
			return false;
		}
	
		public function fullscreen():void{
			if(this.stage && this.parent){
				this.stage.removeEventListener( FullScreenEvent.FULL_SCREEN, this.fullScreenHandler );
				this.stage.addEventListener( FullScreenEvent.FULL_SCREEN, this.fullScreenHandler );

				var stageInstance:Stage = this.stage;
				this.oldParent = this.parent;
				this.oldChildIndex = this.parent.getChildIndex( this );
				
				var playerInstance:YouTubePlayer = this.parent.removeChild( this ) as YouTubePlayer;
				stageInstance.addChild( playerInstance );
				
				this.oldBounds = this.getBounds(this.stage);
				this.stage.displayState = StageDisplayState.FULL_SCREEN;
				this.width = this.stage.width;
				this.height = this.stage.height;
				this.x = 0;
				this.y = 0;
			}
		}
		
		protected function fullScreenHandler(event:FullScreenEvent):void{
			if(!event.fullScreen){
				this.width = this.oldBounds.width;
				this.height = this.oldBounds.height;
				this.x = this.oldBounds.x;
				this.y = this.oldBounds.y;
				this.oldParent.addChildAt(this, this.oldChildIndex);
				this.stage.removeEventListener( FullScreenEvent.FULL_SCREEN, this.fullScreenHandler );
			}
		}
		
		override protected function createChildren():void{
			super.createChildren();
			this.loader.contentLoaderInfo.addEventListener(Event.INIT, onLoaderInit);
			this.loader.load(new URLRequest(PLAY_URL));
		}
		
		override public function invalidateProperties():void{
			super.invalidateProperties();
			if(this.player){
				var reset:Boolean =  false;
				if(this.videoIDChanged){
					this.stop();
					this.player.loadVideoById(this.videoID);
					reset = true;
					this.videoIDChanged = false;
				}
				
				/*
				Doesn't seem to work
				TypeError: Error #1006: loadVideoByUrl is not a function.
				if(this.videoURLChanged){
					this.stop();
					this.player.loadVideoByUrl(this.videoURL);
					reset = true;
					this.videoURLChanged = false;
				}
				*/
				
				if(reset){
					if(!this.autoPlay){
						this.pause();
					}
					this.volumeChanged = true;
				}
				
				
				if(this.playbackQualityChanged){
					this.player.setPlaybackQuality(this._playbackQuality);
					this.playbackQualityChanged = false;
				}
				
				if(this.volumeChanged){
					player.setVolume(this.volume * 100)
					this.volumeChanged = false;
				}
			}
		}
		
		override public function invalidateSize():void{
			super.invalidateSize();
		}
		
		override protected function updateDisplayList(unscaledWidth:Number, unscaledHeight:Number):void{
			super.updateDisplayList(unscaledWidth, unscaledHeight);
			if(this.player){
				this.player.setSize(this.width, this.height);
			}
		}
		
		private function onLoaderInit(event:Event):void {
		    this.addChild(this.loader);
		    
		    this.loader.content.addEventListener("onReady", onPlayerReady);
		    this.loader.content.addEventListener("onError", onPlayerError);
		    this.loader.content.addEventListener("onStateChange", onPlayerStateChange);
		    this.loader.content.addEventListener("onPlaybackQualityChange",  onVideoPlaybackQualityChange);
		}
		
		private function onPlayerReady(event:Event):void {
		    this.player = loader.content;
		    this.invalidateProperties();
		    this.invalidateDisplayList();
		}
		
		private function onPlayerError(event:Event):void {
		    // Event.data contains the event parameter, which is the error code
		    this.dispatchEvent(event);
		}
		
		private var updateInterval:Number = 0;
		private function onPlayerStateChange(event:Event):void {
		    // Event.data contains the event parameter, which is the new player state
		    var stateIndex:Number = event["data"];
		     
		     switch(stateIndex){
		     	case 0: clearInterval(this.updateInterval);break;
		     	case 1: updateInterval = setInterval(function():void{
		     		currentTime = player.getCurrentTime()*1000;
		     	}, 500); break;
		     	case 3: this.duration = this.player.getDuration()*1000; break;
		     }
		     
		     this.dispatchEvent(event);
		}
		
		private function onVideoPlaybackQualityChange(event:Event):void {
		    // Event.data contains the event parameter, which is the new video quality
		    this.dispatchEvent(event);
		} 
	}
}