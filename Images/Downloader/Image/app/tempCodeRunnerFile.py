 # self.workForPod(json_object)
            
            # # If work was successful then update history table
            # self.updateHistoryTable(self.grp_id, 'completed', "")

            # # Update group status
            # update_group_query = """UPDATE grupos SET status = %s WHERE id = %s"""
            # self.mariadbCursor = self.MariaClient.cursor(prepared = True)
            # self.mariadbCursor.execute(update_group_query, ('completed',self.grp_id,))
            # self.MariaClient.commit()

            # # Send message to output queue for next component
            # self.sendMessage(RABBITUSER, RABBITPASS, RABBITHOST, RABBITPORT, RABBITQUEUENAMEINPUT)

            # # Feed metrics
            # self.metrics()

            # print(f"{bcolors.OK} Downloader: {bcolors.RESET} Process finished")