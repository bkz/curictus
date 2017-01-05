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

﻿package
{
	import flash.events.*;
    import flash.geom.Matrix;
    import flash.ui.Keyboard;
    import org.papervision3d.core.math.Matrix3D;
    
    import mx.collections.ArrayCollection;
    import mx.utils.ObjectProxy;
    
    import org.papervision3d.materials.special.ParticleMaterial;
    import org.papervision3d.typography.Font3D;
    import org.papervision3d.materials.special.Letter3DMaterial; 
	
	import mx.core.UIComponent;
    import mx.events.ResizeEvent;
    import mx.controls.Alert;
		
	import org.papervision3d.cameras.Camera3D;
	import org.papervision3d.render.BasicRenderEngine;
    import org.papervision3d.scenes.Scene3D;
    import org.papervision3d.view.Viewport3D;

    import org.papervision3d.core.geom.renderables.Vertex3D;
    import org.papervision3d.core.geom.Lines3D;
    import org.papervision3d.core.geom.renderables.Line3D;
    
    import org.papervision3d.objects.DisplayObject3D;
    import org.papervision3d.materials.ColorMaterial;
    import org.papervision3d.materials.special.LineMaterial;

    import org.papervision3d.core.geom.Particles;
    import org.papervision3d.core.geom.renderables.Particle;

    import org.papervision3d.typography.Text3D;
    import org.papervision3d.typography.fonts.HelveticaBold;
    
	public class KinectPlot extends UIComponent
	{				
        include "defs.as"

        private var renderer:BasicRenderEngine = new BasicRenderEngine();
        private var scene:Scene3D = new Scene3D();
        private var camera:Camera3D = new Camera3D;
        private var viewport:Viewport3D;
        
        private var font:Font3D =  new HelveticaBold();
        private var fontMaterial: Letter3DMaterial = new Letter3DMaterial(0x333333, 0.9 ); 
        
		public var chartContainer:DisplayObject3D;
        public var chart:DisplayObject3D;
        
        private static const MAX_SIZE : Number = 1000; 
        private static const AXIS_SIZE : Number = 150;     
        
        [Bindable]
        public var chartX:int = 0;
        [Bindable]
        public var chartY:int = 0;
        [Bindable]
        public var chartZ:int = 0;
        [Bindable]
        public var cameraFov:int = 15;
        
		public function KinectPlot() 
		{
			super();
				            
			viewport = new Viewport3D(this.width, this.height);
			this.addChild(viewport);
                                                      
            fontMaterial.doubleSided = true;

            this.addEventListener(Event.RESIZE, onStageResize);
		}	

        public function clear(): void {
           if (chartContainer) {
                scene.removeChild(chartContainer)                
            }
            
            renderScene();
        }
        
        public function rotate(n:Number):void {
            if (chartContainer)
                chartContainer.rotationY = n % 360;
            renderScene();
        }
        
		public function loadSession(data:ObjectProxy, plotEvents:Array = null, plotErrors:Array = null, drawAxis:Boolean = true, drawLabels:Boolean = true, fov:Number = 15, rotationX:Number = 0, rotationZ:Number = 0, rotationY:Number = 0):void
		{	
            var i:int;

            clear();
            
            cameraFov = fov;                       
            camera.y = 20;
            
            chartContainer = new DisplayObject3D("Chart Container");
            chartContainer.rotationX = rotationX;
            chartContainer.rotationY = rotationY;
            chartContainer.rotationZ = rotationZ;

            chart = new DisplayObject3D("Chart");            
                       
            var defaultMaterial : LineMaterial = new LineMaterial( 0x444444, .35 );
            var xAxisMaterial   : LineMaterial = new LineMaterial( 0x1B95D9, .5  );
            var yAxisMaterial   : LineMaterial = new LineMaterial( 0x1B95D9, .5  );
            var zAxisMaterial :   LineMaterial = new LineMaterial( 0x1B95D9, .5  );

            if (drawAxis) {
                var axes : Lines3D = new Lines3D( defaultMaterial, "Axes" );
                axes.addLine( new Line3D( axes, xAxisMaterial, 2, new Vertex3D( -AXIS_SIZE, 0, 0 ), new Vertex3D( AXIS_SIZE, 0, 0 ) ));
                axes.addLine( new Line3D( axes, yAxisMaterial, 2, new Vertex3D( 0,-AXIS_SIZE/2,0 ), new Vertex3D( 0,AXIS_SIZE/2,0 ) ));
                if (rotationZ !== 0)
                    axes.addLine( new Line3D( axes, zAxisMaterial, 2, new Vertex3D( 0,0,-AXIS_SIZE ), new Vertex3D( 0,0,AXIS_SIZE ) ));          
                chart.addChild( axes );
                           
                var xAxisLabel:Text3D = new Text3D("X", font, fontMaterial, "xAxisLabel")
                xAxisLabel.x = AXIS_SIZE + 10;
                xAxisLabel.y = 0;
                xAxisLabel.z = 0;
                xAxisLabel.rotationX = -rotationX;
                xAxisLabel.rotationY = -rotationY;
                xAxisLabel.rotationZ = -rotationZ;
                xAxisLabel.scale = 0.08;
                chart.addChild(xAxisLabel);

                var yAxisLabel:Text3D = new Text3D("Y", font, fontMaterial, "yAxisLabel")
                yAxisLabel.x = 0;
                yAxisLabel.y = -AXIS_SIZE/2 - 10;
                yAxisLabel.z = 0;
                yAxisLabel.rotationX = -rotationX;
                yAxisLabel.rotationY = -rotationY;
                yAxisLabel.rotationZ = -rotationZ;
                yAxisLabel.scale = 0.08;
                chart.addChild(yAxisLabel);

                if (rotationZ !== 0) {
                    var zAxisLabel:Text3D = new Text3D("Z", font, fontMaterial, "zAxislabel")
                    zAxisLabel.x = 0;
                    zAxisLabel.y = 0;
                    zAxisLabel.z = -AXIS_SIZE - 20;
                    zAxisLabel.rotationX = -rotationX;
                    zAxisLabel.rotationY = -rotationY;
                    zAxisLabel.rotationZ = -rotationZ;                    
                    zAxisLabel.scale = 0.08;
                    chart.addChild(zAxisLabel);
                }
            }

            var lastVertex:Vertex3D = null;
            var currentVertex:Vertex3D = null;
                        
            var lines : Lines3D = new Lines3D( defaultMaterial, "Lines" );            
            chart.addChild( lines );
            
            var points:ArrayCollection = data["kinematics"];
            for(i = 0; i<points.length; i++)
            {
                lastVertex = currentVertex;
                currentVertex = new Vertex3D();
                
                currentVertex.x = points.getItemAt(i)["p_x"] * MAX_SIZE;
                currentVertex.y = points.getItemAt(i)["p_y"] * MAX_SIZE;
                currentVertex.z = -points.getItemAt(i)["p_z"] * MAX_SIZE;
                
                if (lastVertex !== null ) {
                    var line : Line3D = new Line3D( lines, defaultMaterial, 2, lastVertex, currentVertex );
                    lines.addLine( line );
                }
            }
            
            var particleSize : Number = 5; 
            var particleMaterialOK  : ParticleMaterial = new ParticleMaterial(0xA5BC4E, 0.9, ParticleMaterial.SHAPE_CIRCLE); 
            var particleMaterialERR : ParticleMaterial = new ParticleMaterial(0xC91452, 0.6, ParticleMaterial.SHAPE_SQUARE); 
            var particles : Particles = new Particles(); 
            chart.addChild(particles);
            
            var pointVertex:Vertex3D = new Vertex3D();            
            var events:ArrayCollection = data["events"];
            for(i = 0; i<events.length; i++)
            {
                pointVertex = new Vertex3D();                
                pointVertex.x = events.getItemAt(i)["x"] * MAX_SIZE;
                pointVertex.y = events.getItemAt(i)["y"] * MAX_SIZE;
                pointVertex.z = -events.getItemAt(i)["z"] * MAX_SIZE;

                var drawTooltip:Boolean = false;
                
                if (plotEvents && plotEvents.indexOf( events.getItemAt(i)["id"] ) !== -1)
                {
                    var p1 : Particle = new Particle(particleMaterialOK, particleSize, pointVertex.x, pointVertex.y, pointVertex.z);
                    particles.addParticle(p1);                                                                         
                    drawTooltip = true;
                }
                                    
                if (plotErrors && plotErrors.indexOf( events.getItemAt(i)["id"] ) !== -1)
                {
                    var p2: Particle = new Particle(particleMaterialERR, particleSize, pointVertex.x, pointVertex.y, pointVertex.z);
                    particles.addParticle(p2);                                                                         
                    drawTooltip = true;
                }        
                
                if (drawLabels && drawTooltip == true) {
                    var t:String = sprintf("%2.2fs", events.getItemAt(i)["timestamp"]);
                    
                    var tooltipLabel:Text3D = new Text3D(t, font, fontMaterial)
                    tooltipLabel.x = pointVertex.x + 10;
                    tooltipLabel.rotationX = -chartContainer.rotationX;
                    tooltipLabel.y = pointVertex.y;
                    tooltipLabel.rotationY = chartContainer.rotationY;
                    tooltipLabel.z = pointVertex.z;
                    tooltipLabel.rotationZ = chartContainer.rotationZ;
                    tooltipLabel.scale = 0.05;
                    chart.addChild(tooltipLabel);
                }
            }
            
            chartContainer.addChild(chart);
            scene.addChild(chartContainer);
            renderScene();            

            /*
            stage.addEventListener(KeyboardEvent.KEY_DOWN, 
                function(event:KeyboardEvent):void {
                    switch(event.keyCode) {
                        case Keyboard.UP:
                            chartContainer.rotationX -= 1;
                            break;
                         case Keyboard.DOWN:
                            chartContainer.rotationX += 1;
                            break;
                         case Keyboard.LEFT:
                            chartContainer.rotationY += 1;
                            break;
                         case Keyboard.RIGHT:
                            chartContainer.rotationY -= 1;
                            break;               
                         case Keyboard.PAGE_UP:
                            chartContainer.rotationZ += 1;
                            break;
                         case Keyboard.PAGE_DOWN:
                            chartContainer.rotationZ -= 1;
                            break;               
                        case Keyboard.F1:
                           chart.transform = new Matrix3D();
                           chartContainer.rotationX = chartContainer.rotationY = chartContainer.rotationZ= 0;
                           break;                           
                        case Keyboard.F2:
                           chart.transform = new Matrix3D(data["transform"].source);
                           chartContainer.rotationX = chartContainer.rotationY = chartContainer.rotationZ= 0;
                           break;
                        case Keyboard.F3:
                           cameraFov += 1;
                           break;                           
                        case Keyboard.F4:
                           cameraFov -= 1;
                           break;
                         default:
                            break;   
                    }
                })
            */
        }
        
        private function renderScene():void
        {           
            renderer.renderScene(scene, camera, viewport);  
            
            if (chartContainer) {
                chartX = chartContainer.rotationX;
                chartY = chartContainer.rotationY;
                chartZ = chartContainer.rotationZ;
            }
        }

        private function onStageResize(event:ResizeEvent):void
		{
            if (viewport != null)
			{
                viewport.viewportWidth = this.width;
                viewport.viewportHeight = this.height;

                camera.update(viewport.sizeRectangle);
                camera.fov = cameraFov;
                
                renderScene();
            }            
        }		
	}
}
