$(document).ready(function() { //To run code as soon as the document is ready to be manipulated
    // $('form').on('submit', function(event) {
    $('#compute').on('click', function(event) {
        $('#image').prop("hidden", true)
        $.ajax({
            data : { //JSON Data Type for procces.py
                pipe_unit :  $('#pipe_unit').val(),
                inletD :     $('#inletD').val(),
                outletD :    $('#outletD').val(),
                liquid :     $('#liquid').val(), 
                flow_unit :  $('#flow_unit').val(),
                press_unit : $('#press_unit').val(),
                temp_unit :  $('#temp_unit').val(),

                check_Min :  $('#CheckMin').is(':checked'),
                flow_Min   : $('#flow_Min').val(), 
                P1_Min :     $('#P1_Min').val(),
                P2_Min :     $('#P2_Min').val(), 
                deltaP_Min : $('#deltaP_Min').val(),
                temp_Min :   $('#temp_Min').val(), 
                
                flow_Op   : $('#flow_Op').val(), 
                P1_Op :     $('#P1_Op').val(),
                P2_Op :     $('#P2_Op').val(), 
                deltaP_Op : $('#deltaP_Op').val(),
                temp_Op :   $('#temp_Op').val(), 

                check_Max :  $('#CheckMax').is(':checked'),
                flow_Max   : $('#flow_Max').val(), 
                P1_Max :     $('#P1_Max').val(),
                P2_Max :     $('#P2_Max').val(), 
                deltaP_Max : $('#deltaP_Max').val(),
                temp_Max :   $('#temp_Max').val(), 
            }, 
            type : 'POST', 
            url : '/process'
        })
        .done(function(data) {
            if (data.error){
                $('#errorAlert').text(data.error).show();
                $('#successAlert').hide();
                $('#ResultMin').hide();
            }
            else {
                $('#ResultMin').hide();
                $('#ResultMax').hide();
                $('#ResultOp').hide();
                $('#successAlert').text("Liquid Gf: " + data.rho + " | viscosity: " + data.mu + " centipoise |"+ "critical pressure: " + data.Pc + " psi a |" + " vapor pressure: " + data.Psat + " psi a").show();
                if (data.Cv_Op) {$('#ResultOp').text("Cv: " + data.Cv_Op).show();
                                $('#ResultOp').val(data.Cv_Op) 
                                $('#reqCv_Op').text(data.Cv_Op)}
                if (data.Cv_Min) {$('#ResultMin').text("Cv: " + data.Cv_Min).show();
                                  $('#ResultMin').val(data.Cv_Min)
                                  $('#reqCv_Min').text(data.Cv_Min) }
                if (data.Cv_Max) {$('#ResultMax').text("Cv: " + data.Cv_Max).show();
                                  $('#ResultMax').val(data.Cv_Max) 
                                  $('#reqCv_Max').text(data.Cv_Max) }
                $('#errorAlert').hide();
            }
        });
        event.preventDefault();
    });


    //Enable additional input procces based on status check box input
    $('#CheckMin').click(function () {
        var checked = this.checked;
        console.log(checked);
        
        $('.input_min').each(function () {
            $(this).prop('disabled', !checked);
        });
        if (!checked) {
            $('.input_min').each(function () {
                $(this).val('');
                $('#ResultMin').hide();
                $('#reqCv_Min').text('-')
                $('#travelMin').text('-')
                $('#percentageCvMin').text('-')
            });
        }
        else { //enable input Min logic for pressure drop and Outlet pressure


            if ($('#radio_deltaP').prop('checked')) {
                $('#P2_Min').prop('disabled', true);
                $('#deltaP_Min').prop('disabled', false);
            } 
            else {
                $('#P2_Min').prop('disabled', false);
                $('#deltaP_Min').prop('disabled', true); 
            }

        }
    });

    $('#CheckMax').click(function () {
        var checked = this.checked;
        console.log(checked);
        $('.input_max').each(function () {
            $(this).prop('disabled', !checked);
        });
        if (!checked) {
            $('.input_max').each(function () {
                $(this).val('');
                $('#ResultMax').hide();
                $('#reqCv_Max').text('-');
                $('#travelMax').text('-');
                $('#percentageCvMax').text('-')
            });
        } 
        else { //enable input Min logic for pressure drop and Outlet pressure
            // console.log($('#radio_deltaP').prop('checked'))
            // console.log($('#radio_P2').prop('checked') )

            if ($('#radio_deltaP').prop('checked')) {
                $('#P2_Max').prop('disabled', true);
                $('#deltaP_Max').prop('disabled', false);
            } 
            else {
                $('#P2_Max').prop('disabled', false);
                $('#deltaP_Max').prop('disabled', true); 
            }

        }
  
    });

    //logic to selection pressure drop input based on Outlet pressure or direct Pressure Drop
    $('#radio_deltaP').click(function(){
        $('#P2_Op').prop('disabled', true);
        $('#deltaP_Op').prop('disabled', false);
        if ($('#CheckMin').prop('checked')) {
            console.log('Cambio en radio delta ON & Check min is ON')
            $('#P2_Min').prop('disabled', true);
            $('#deltaP_Min').prop('disabled', false); 
        }
        if ($('#CheckMax').prop('checked')) {
            console.log('Cambio en radio delta ON & Check min is ON')
            $('#P2_Max').prop('disabled', true);
            $('#deltaP_Max').prop('disabled', false); 
        }
    });
    $('#radio_P2').click(function(){
        $('#P2_Op').prop('disabled', false);
        $('#deltaP_Op').prop('disabled', true); 
        if ($('#CheckMin').prop('checked')) {
            console.log('Cambio en radio P2 ON & Check min is ON')
            $('#P2_Min').prop('disabled', false);
            $('#deltaP_Min').prop('disabled', true); 
        }
        if ($('#CheckMax').prop('checked')) {
            console.log('Cambio en radio P2 ON & Check min is ON')
            $('#P2_Max').prop('disabled', false);
            $('#deltaP_Max').prop('disabled', true); 
        }
    });
    //if user enters pressure P1 : PDrop is automatically filled an vicseversa
    $("#P2_Op").on("input", function(){
        $('#deltaP_Op').val( $('#P1_Op').val() - $(this).val());
    });
    $('#deltaP_Op').on("input", function(){
        $('#P2_Op').val( $('#P1_Op').val() - $(this).val());
    });

    $('#P2_Min').on("input", function(){
        $('#deltaP_Min').val( $('#P1_Min').val() - $(this).val());
    });
    $('#deltaP_Min').on("input", function(){
        $('#P2_Min').val( $('#P1_Min').val() - $(this).val());
    });

    $('#P2_Max').on("input", function(){
        $('#deltaP_Max').val( $('#P1_Max').val() - $(this).val());
    });
    $('#deltaP_Max').on("input", function(){
        $('#P2_Max').val( $('#P1_Max').val() - $(this).val());
    });


    //NOMINAL PIPE SIZE & SCHEDULE SELECTION

    //Once selected Inlet Pipe Outlet is selected by default
    $('#inletD').change(function() {
        $("#outletD").val($('#inletD').val())
        $.ajax({
            type:'POST', 
            url : '/pipe',
            data : {'OD_in' : $('#inletD').val() }
        })
        .done(function(data) { 
            data = data.replace('[','');
            data = data.replace(']','');
            dataJson = jQuery.parseJSON( data );
            delete dataJson['NPS_in'];
            $('#schInlet').empty();
            $('#schOutlet').empty();
            $('#schInlet').append('<option disabled selected>Select Schd</option>');
            $('#schOutlet').append('<option disabled selected>Select Schd</option>');
            $.each(dataJson, function( key, value ) {
                // console.log( key + ": " + value );
                console.log('<option value=' + value +'>' + key + '</option>'  );
                $('#schInlet').append('<option value=' + value +'>' + key + '</option>' );
                $('#schOutlet').append('<option value=' + value +'>' + key + '</option>' );
                // $(#schInlet).text(key)


              });
        });

    });

    //Once schedule is selected values are shown & schedule for outlet by default
    $('#schInlet').change(function() {
        $('#ODin').prop("hidden", false);
        $('#wallThick_in').prop("hidden", false)
        $('#ODin').val( "O.D. (in): " + $('#inletD').val())
        $('#wallThick_in').val( "wall Thick (in): " + $('#schInlet').val())
        $('#schOutlet').val($('#schInlet').val())

    });
    

    //VALVE SELECTION - 

    //valve model selection displays proper valve size drop down menu
    $('#valve_model').change(function() {
        console.log("Cambio de estado en valvula")
        $("#ratedCv_label").prop("hidden", true)
        $("#ratedCv").prop("hidden", true)
        $('#image').prop("hidden", true)

        $.ajax({
            type:'POST', 
            url : '/valve',
            data : {'model' : $('#valve_model').val() }
        })
        .done(function(data) { //once valve is selected Drop Down Valve Size available is populated
            $('#valve_size').empty();
            $('#valve_size').append('<option disabled selected>Select Valve Size</option>');
            for (var i=0; i<data['lista'].length; i++){
                $('#valve_size').append('<option value=' + data['lista'][i] +'>' + data['lista'][i] + ' in </option>' );
            }
        });
    });

    //once selected valve size all Rated Cv for this valve size MUST be available for user selection 
    $('#valve_size').change(function() {
        $('#image').prop("hidden", true)
        $.ajax({
            type:'POST', 
            url : '/rated_Cv',
            data : {'size' : $('#valve_size').val() }
        })
        .done(function(data) {
            console.log('fue a rated_Cv and returned data')
            $('#ratedCv').empty();
            $('#ratedCv').append('<option disabled selected>Select</option>');
            for (var i=0; i<data['100%'].length; i++)  //populate ratedCv with 100% values for user selection
                $('#ratedCv').append('<option value=' + data['100%'][i] +'>' + data['100%'][i] + '</option>' );
            $("#ratedCv_label").prop("hidden", false)
            $("#ratedCv").prop("hidden", false)
        });

    });

    //finally ratedCv can be selected to fit Procces data
    $('#ratedCv').change(function() {
        $("#valve_sizing").prop("hidden", false)
        $('#image').prop("hidden", true)
        console.log("Now finally we are ready for serious calculation ...")
    });



    //Compute Cv with Valve selected
    $('#valve_sizing').on('click', function() {
         console.log($('#ratedCv').val())

        //check calculated Cv already performed and formatted for server in Cv_computed array
        Cv_computed = [Number($('#ResultOp').val()), 0, 0]
        if ($('#CheckMin').prop('checked')) {
             Cv_computed[1] =  Number($('#ResultMin').val());
        }
        if ($('#CheckMax').prop('checked')) {
            Cv_computed[2] = Number($('#ResultMax').val());
        }

       if (Cv_computed[0] =="")  {
           console.log('No hay datos para calcular')
       }
       else{
            $.ajax({
                type:'POST', 
                url : '/valve_sizing',
                data : {
                    'ratedCv' : $('#ratedCv').val(),
                    'Cv_required' : JSON.stringify(Cv_computed), 
                    'valve_size' : $('#valve_size').val(),
                    'valve_model' : $('#valve_model').val(),

                    //data from input proccess 
                    pipe_unit :  $('#pipe_unit').val(),
                    inletD :     $('#inletD').val(),
                    outletD :    $('#outletD').val(),
                    liquid :     $('#liquid').val(), 
                    flow_unit :  $('#flow_unit').val(),
                    press_unit : $('#press_unit').val(),
                    temp_unit :  $('#temp_unit').val(),
    
                    check_Min :  $('#CheckMin').is(':checked'),
                    flow_Min   : $('#flow_Min').val(), 
                    P1_Min :     $('#P1_Min').val(),
                    P2_Min :     $('#P2_Min').val(), 
                    deltaP_Min : $('#deltaP_Min').val(),
                    temp_Min :   $('#temp_Min').val(), 
                    
                    flow_Op   : $('#flow_Op').val(), 
                    P1_Op :     $('#P1_Op').val(),
                    P2_Op :     $('#P2_Op').val(), 
                    deltaP_Op : $('#deltaP_Op').val(),
                    temp_Op :   $('#temp_Op').val(), 
    
                    check_Max :  $('#CheckMax').is(':checked'),
                    flow_Max   : $('#flow_Max').val(), 
                    P1_Max :     $('#P1_Max').val(),
                    P2_Max :     $('#P2_Max').val(), 
                    deltaP_Max : $('#deltaP_Max').val(),
                    temp_Max :   $('#temp_Max').val()


                    }
            })
            .done(function(data) {
                console.log('go to server and arrives OK !! ')
                //update grapic of valve calculations and update table
                d = new Date();
                $('#image').prop('src', "./static/docs/grafico.png?"+d.getTime() );
                $('#image').prop("hidden", false)
                //data to populate results table
                $('#reqCv_Op').text(data.CvOp)
                $('#reqCv_Min').text(data.CvMin)
                $('#reqCv_Max').text(data.CvMax)
                $('#travelOp').text(data.travelOp)
                $('#travelMin').text(data.travelMin)
                $('#travelMax').text(data.travelMax)
                $('#percentageCvOp').text(data.percentageCvOp)
                $('#percentageCvMin').text(data.percentageCvMin)
                $('#percentageCvMax').text(data.percentageCvMax)
                $('#FLOp').text(data.FLOp)
                $('#FLMin').text(data.FLMin)
                $('#FLMax').text(data.FLMax)

        });  
        }   
    
    });


});


