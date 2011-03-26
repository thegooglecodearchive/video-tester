#include <gst/gst.h>
#include <gst/rtsp-server/rtsp-server.h>
#include <string.h>

int main (int argc, char *argv[])
{
  GMainLoop *loop;
  GstRTSPServer *server;
  GstRTSPMediaMapping *mapping;
  GstRTSPMediaFactory *factory;
  gchar *pipe, *url;
  int i, j, cont;

  gst_init (&argc, &argv);

  if (argc < 7 || strcmp(argv[1], "-p") != 0 || strcmp(argv[3], "-f") != 0 || strcmp(argv[5], "-b") != 0 || strcmp(argv[7], "-v") != 0) {
    g_print ("usage: %s -p <port> -f <framerate> -b <bitrate(kbps)> -v <video1> <video2> ...\n", argv[0]);
    return -1;
  }

  loop = g_main_loop_new (NULL, FALSE);

  /* create a server instance */
  server = gst_rtsp_server_new ();
  gst_rtsp_server_set_service (server, argv[2]);
  
  /* map media */
  cont = 0;
  for (i = 8; i < argc; i++) {
    for (j = 0; j <= 3; j++) {
      switch (j){
	case 0: /* h263 */
	  pipe = g_strdup_printf("( filesrc location=%s ! decodebin2 ! videorate ! video/x-raw-yuv,framerate=%s/1 ! ffenc_h263 bitrate=%s000 ! rtph263pay name=pay0 )", argv[i], argv[4], argv[6]);
	  url = g_strdup_printf("/video%d.h263", cont);
	  //g_print ("%s\n", pipe);
	  break;
	case 1: /* h264 */
	  pipe = g_strdup_printf("( filesrc location=%s ! decodebin2 ! videorate ! video/x-raw-yuv,framerate=%s/1 ! x264enc bitrate=%s ! rtph264pay name=pay0 )", argv[i], argv[4], argv[6]);
	  url = g_strdup_printf("/video%d.h264", cont);
	  //g_print ("%s\n", pipe);
	  break;
	case 2: /* mpeg4 */
	  pipe = g_strdup_printf("( filesrc location=%s ! decodebin2 ! videorate ! video/x-raw-yuv,framerate=%s/1 ! ffenc_mpeg4 bitrate=%s000 ! rtpmp4vpay name=pay0 )", argv[i], argv[4], argv[6]);
	  url = g_strdup_printf("/video%d.mpeg4", cont);
	  //g_print ("%s\n", pipe);
	  break;
	case 3: /* theora */
	  pipe = g_strdup_printf("( filesrc location=%s ! decodebin2 ! videorate ! video/x-raw-yuv,framerate=%s/1 ! theoraenc bitrate=%s ! rtptheorapay name=pay0 )", argv[i], argv[4], argv[6]);
	  url = g_strdup_printf("/video%d.theora", cont);
	  //g_print ("%s\n", pipe);
	  break;
      }
      /* get the mapping for this server, every server has a default mapper object
      * that be used to map uri mount points to media factories */
      mapping = gst_rtsp_server_get_media_mapping (server);

      /* make a media factory for a test stream. The default media factory can use
      * gst-launch syntax to create pipelines. 
      * any launch line works as long as it contains elements named pay%d. Each
      * element with pay%d names will be a stream */
      factory = gst_rtsp_media_factory_new ();
      gst_rtsp_media_factory_set_launch (factory, pipe);

      gst_rtsp_media_factory_set_shared (factory, TRUE);
      gst_rtsp_media_factory_set_eos_shutdown (factory, TRUE);

      /* attach the test factory to the /test url */
      gst_rtsp_media_mapping_add_factory (mapping, url, factory);

      /* don't need the ref to the mapper anymore */
      g_object_unref (mapping);
      g_free (url);
      g_free (pipe);
    }
    cont = cont + 1;
  }

  /* attach the server to the default maincontext */
  if (gst_rtsp_server_attach (server, NULL) > 0)
    /* start serving */
    g_main_loop_run (loop);

  return 0;
}