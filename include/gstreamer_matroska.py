    def receiver(self):
        vtLog.info("Starting GStreamer receiver...")
        self.pipeline = parse_launch('rtspsrc name=source ! matroskamux ! filesink name=sink')
        source = self.pipeline.get_by_name('source')
        sink = self.pipeline.get_by_name('sink')
        source.props.location = self.uri
        source.props.protocols = self.conf['protocols']
        location = self.conf['tempdir'] + self.conf['num'] + '.mkv'
        sink.props.location = location
        self.__play()
        self.__decode(location)
        vtLog.info("GStreamer receiver stopped")
    
    def reference(self):
        vtLog.info("Making reference...")
        self.__decode(self.video, '_ref_original', True)
        self.pipeline = parse_launch('filesrc name=source ! decodebin2 ! ' + self.encoder + ' bitrate=' + self.bitrate + ' ! matroskamux ! filesink name=sink')
        source = self.pipeline.get_by_name('source')
        sink = self.pipeline.get_by_name('sink')
        location = self.video
        source.props.location = location
        location = self.conf['tempdir'] + self.conf['num'] + '_ref.mkv'
        sink.props.location = location
        self.__play()
        self.__decode(location, '_ref')
        vtLog.info("Reference made")
    
    def __decode(self, location, name='', caps=False):
        self.pipeline = parse_launch('filesrc name=source ! decodebin2 ! videorate ! video/x-raw-yuv,framerate=25/1 ! filesink name=sink')
        source = self.pipeline.get_by_name('source')
        sink = self.pipeline.get_by_name('sink')
        source.props.location = location
        location = self.conf['tempdir'] + self.conf['num'] + name + '.yuv'
        if caps:
            pad = sink.get_pad("sink")
            pad.connect("notify::caps", self.__notifyCaps)
        self.__play()